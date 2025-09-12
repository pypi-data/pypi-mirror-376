from __future__ import annotations

import json
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

from ..redis_client import get_redis


@dataclass(frozen=True)
class StreamMsg:
    """Redis流消息数据类
    
    用于表示从Redis流中读取的消息, 包含流名称、消息ID、字段数据和元数据。
    使用frozen=True确保消息对象不可变, 保证线程安全。
    
    Attributes:
        stream: 消息所属的流名称
        msg_key: 消息的唯一标识符
        payload: 消息的字段数据，可以是JSON字符串或原生字符串
        meta: 消息的元数据，用于存储额外的信息如处理时间、来源等
    """
    stream: str
    payload: str
    msg_key: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class RedisStreamsClient:
    """Redis流的高级客户端, 支持消费者组功能
    
    这是一个基于Redis流的高级封装客户端, 提供了完整的流处理功能。
    
    主要功能：
    - xadd: 向流中推送消息
    - xreadgroup: 以消费者组的方式从多个流中读取消息
    - 逐消息回调处理, 成功时自动确认
    - 可选的待处理消息声明功能（高级用法）
    
    适用场景：
    - 消息队列和事件流处理
    - 多消费者负载均衡
    - 可靠的消息传递和处理
    - 实时数据流分析
    """

    def __init__(self, *, redis_client=None) -> None:
        """初始化Redis流客户端
        
        Args:
            redis_client: Redis客户端实例, 如果未提供则使用默认客户端
        """
        self.redis = redis_client or get_redis()

    def push(self, msg: StreamMsg, *, maxlen: int | None = None) -> str:
        """向指定流推送消息
        
        Args:
            msg: 要推送的消息对象（payload可以是JSON字符串或原生字符串）
            maxlen: 流的最大长度限制, 超出时自动删除最旧消息
                   - None: 无限制（默认）
                   - 正整数: 保留最新的N条消息
            
        Returns:
            str: 新创建消息的ID
        """
        # 将消息的 payload 转为 xadd 所需的字段字典
        fields: dict[str, Any]
        if msg.payload:
            try:
                parsed = json.loads(msg.payload)
                if isinstance(parsed, dict):
                    fields = parsed
                else:
                    # 非对象JSON（如列表/数字/字符串），统一放入单字段
                    fields = {"payload": msg.payload}
            except Exception:
                # 非JSON字符串，作为原始payload字段
                fields = {"payload": msg.payload}
        else:
            fields = {}

        # 将 meta 放入保留字段 __meta（JSON 字符串形式）
        if msg.meta:
            try:
                fields["__meta"] = json.dumps(msg.meta)
            except Exception:
                # 兜底：不可序列化则转字符串包装
                fields["__meta"] = json.dumps({"raw": str(msg.meta)})

        args: dict[str, Any] = {"fields": fields}
        if maxlen is not None:
            # 为了性能使用近似修剪
            args["maxlen"] = maxlen
            args["approximate"] = True
        msg_key: str = self.redis.xadd(msg.stream, **args)
        return msg_key

    def ensure_group(self, stream: str, group: str) -> None:
        """确保消费者组存在, 如果不存在则创建
        
        Args:
            stream: 流名称
            group: 消费者组名称
            
        Note:
            如果消费者组已存在, 会忽略BUSYGROUP错误；
            如果流不存在, 会自动创建流。
        """
        try:
            self.redis.xgroup_create(name=stream, groupname=group, id="$", mkstream=True)
        except Exception as e:
            # 消费者组可能已经存在
            msg = str(e)
            if "BUSYGROUP" in msg:
                return
            raise

    def consume(
        self,
        streams: Iterable[str],
        group: str,
        consumer: str,
        callback: Callable[[StreamMsg], bool],
        *,
        discard_on_failure: bool = False,
        count: int = 10,
        block_ms: int = 5000,
        read_new_only: bool = True,
    ) -> None:
        """以消费者组的方式消费多个流并通过回调处理消息
        
        这是一个长期运行的方法, 会持续监听指定的流并处理新消息。
        支持多流并发消费、条件确认等功能。
        
        Args:
            streams: 要消费的流名称列表
            group: 消费者组名称
            consumer: 当前消费者的名称（在组内唯一）
            callback: 消息处理函数, 接收StreamMsg对象, 返回bool值
                     - 返回True: 确认消息
                     - 返回False: 不确认消息, 消息可被重新处理
            discard_on_failure: callback处理失败时是否直接丢弃消息, 默认False
                    - True: callback抛出异常时直接确认并丢弃消息
                    - False: callback抛出异常时不确认消息, 消息可被重新处理
            count: 每次读取的最大消息数量, 默认10
                   - 值越大, 批处理效率越高, 但内存占用更多
                   - 值越小, 响应更及时, 但可能增加Redis调用次数    
            block_ms: 阻塞等待新消息的时间（毫秒）, 默认5000; 当没有新消息时, 阻塞等待的最大时间（毫秒）
                    - 0 ：非阻塞, 立即返回
                    - > 0 ：阻塞指定毫秒数
            read_new_only: - 控制读取消息的起始位置
                    - True ：从 ">" 开始，只读取新消息（推荐）
                    - False ：从 "0" 开始，会读取所有未确认的消息（包括之前失败的）
                    - 使用场景:
                    - 新启动的消费者通常用 True
                    - 故障恢复或处理积压消息时用 False
            
        Note:
            - 如果消费者组不存在, 会自动创建
            - 根据callback返回值决定是否确认消息
            - 此方法会无限循环, 需要外部控制退出
        """
        streams = list(streams)
        for s in streams:
            self.ensure_group(s, group)

        ids = ">" if read_new_only else "0"
        stream_dict = {s: ids for s in streams}

        while True:
            try:
                entries = self.redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams=stream_dict,
                    count=count,
                    block=block_ms,
                )
            except Exception:
                # 错误时进行小幅退避
                time.sleep(0.5)
                continue

            if not entries:
                continue

            for stream_name, messages in entries:
                for msg_key, fields in messages:
                    # 将字节键转换为字符串键，以便 JSON 序列化
                    if fields:
                        str_fields = {k.decode('utf-8') if isinstance(k, bytes) else k: 
                                    v.decode('utf-8') if isinstance(v, bytes) else v 
                                    for k, v in fields.items()}
                        # 提取并解析 __meta
                        meta: dict[str, Any] = {}
                        meta_raw = str_fields.pop("__meta", None)
                        if meta_raw:
                            try:
                                meta = json.loads(meta_raw)
                            except Exception:
                                meta = {"raw": meta_raw}
                        payload_str = json.dumps(str_fields) if str_fields else ""
                    else:
                        payload_str = ""
                        meta = {}
                    # 解码 stream_name 和 msg_key 为 str
                    s_name = stream_name.decode('utf-8') if isinstance(stream_name, bytes) else stream_name
                    m_key = msg_key.decode('utf-8') if isinstance(msg_key, bytes) else msg_key
                    msg = StreamMsg(stream=s_name, msg_key=m_key, payload=payload_str, meta=meta)
                    try:
                        should_ack = callback(msg)
                        if should_ack:
                            self.redis.xack(stream_name, group, msg_key)
                        elif discard_on_failure:
                            self.redis.xack(stream_name, group, msg_key)  # 直接确认并丢弃
                    except Exception as e: # 出错时根据discard_on_failure参数决定是否确认消息
                        print(f"Error processing message {m_key} from stream {s_name}: {e}")
                        if discard_on_failure:
                            self.redis.xack(stream_name, group, msg_key)  # 直接确认并丢弃
                        continue