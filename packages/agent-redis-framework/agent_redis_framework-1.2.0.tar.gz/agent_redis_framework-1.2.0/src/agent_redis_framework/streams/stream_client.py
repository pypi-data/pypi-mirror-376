from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import redis
from ..redis_client import get_redis


@dataclass(frozen=True)
class StreamMsg:
    """Redis流消息数据类
    
    用于表示从Redis流中读取的消息, 包含流名称、消息ID、字段数据和元数据。
    使用frozen=True确保消息对象不可变, 保证线程安全。
    
    Attributes:
        stream: 消息所属的流名称
        payload: 消息的字段数据，可以是JSON字符串或原生字符串
        meta: 消息的元数据，类型为 dict[str, bytes | str | int | float]
    """
    payload: str
    meta: dict[str, bytes | str | int | float] = field(default_factory=dict)


class StreamClient:
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

    def __init__(self, stream: str) -> None:
        """初始化Redis流客户端
        
        Args:
            stream: 流名称
            redis_client: Redis客户端实例, 如果未提供则使用默认客户端
        """
        self.stream: str = stream
        self.redis: redis.Redis = get_redis()


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
            # 修复：使用传入的stream参数而不是self.stream，支持多流操作
            self.redis.xgroup_create(name=stream, groupname=group, id="$", mkstream=True)
        except Exception as e:
            # 消费者组可能已经存在
            msg = str(e)
            if "BUSYGROUP" in msg:
                return
            raise
        
    def push(self, msg: StreamMsg, maxlen: int | None = None) -> str:
        """将消息推送到 Redis Stream。
        存储时将按扁平化字段写入，键前缀为 '__m_'.
        """
        payload_str = msg.payload if isinstance(msg.payload, str) else str(msg.payload)
        fields: dict[str, Any] = {"payload": payload_str}
        # 校验并扁平化 meta
        if msg.meta:
            if not isinstance(msg.meta, dict):
                raise TypeError("StreamMsg.meta must be a dict[str, bytes | str | int | float]")
            for k, v in msg.meta.items():
                if not isinstance(k, str):
                    raise TypeError("StreamMsg.meta keys must be str")
                if not isinstance(v, (bytes, str, int, float)):
                    raise TypeError(
                        f"StreamMsg.meta['{k}'] must be bytes | str | int | float, got {type(v).__name__}")
                fields[f"__m_{k}"] = v
        # 推送
        if maxlen is not None:
            msg_key = self.redis.xadd(self.stream, fields, maxlen=maxlen, approximate=True)  # type: ignore
        else:
            msg_key = self.redis.xadd(self.stream, fields)  # type: ignore
        # 确保返回字符串类型
        if isinstance(msg_key, bytes):
            return msg_key.decode('utf-8')
        return str(msg_key)

    def consume(
        self,
        group: str,
        consumer: str,
        callback: Callable[[str, StreamMsg], bool],
        *,
        discard_on_failure: bool = False,
        count: int = 10,
        block_ms: int = 5000,
        read_new_only: bool = True,
    ) -> None:
        """以消费者组的方式消费当前流并通过回调处理消息
        
        这是一个长期运行的方法, 会持续监听当前流并处理新消息。
        支持条件确认等功能。
        
        Args:
            group: 消费者组名称
            consumer: 当前消费者的名称（在组内唯一）
            callback: 消息处理函数, 接收 (msg_key: str, msg: StreamMsg), 返回 bool
                     - 返回 True: 确认消息
                     - 返回 False: 不确认消息, 消息可被重新处理
            discard_on_failure: callback处理失败时是否直接丢弃消息, 默认 False
                    - True: callback 抛出异常时直接确认并丢弃消息
                    - False: callback 抛出异常时不确认消息, 消息可被重新处理
            count: 每次读取的最大消息数量, 默认 10
                    - 值越大, 批处理效率越高, 但内存占用更多
                    - 值越小, 响应更及时, 但可能增加 Redis 调用次数    
            block_ms: 阻塞等待新消息的时间（毫秒）, 默认 5000; 当没有新消息时, 阻塞等待的最大时间（毫秒）
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
            - 根据 callback 返回值决定是否确认消息
            - 此方法会无限循环, 需要外部控制退出
        """
        # 确保当前流的消费者组存在
        self.ensure_group(self.stream, group)

        ids = ">" if read_new_only else "0"
        stream_dict = {self.stream: ids}

        while True:
            try:
                entries = self.redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams=stream_dict,  # type: ignore
                    count=count,
                    block=block_ms,
                )
            except Exception:
                # 错误时进行小幅退避
                time.sleep(0.5)
                continue

            if not entries:
                continue

            # 由于只处理单一流，简化循环逻辑
            for stream_name, messages in entries:  # type: ignore
                for msg_key, fields in messages:
                    # 将字节键转换为字符串键，以便 JSON 序列化
                    if fields:
                        str_fields = {k.decode('utf-8') if isinstance(k, bytes) else k: 
                                    v.decode('utf-8') if isinstance(v, bytes) else v 
                                    for k, v in fields.items()}
                        # 提取 __m_ 前缀的扁平化 meta
                        meta: dict[str, bytes | str | int | float] = {}
                        to_remove: list[str] = []
                        for k, v in str_fields.items():
                            if isinstance(k, str) and k.startswith("__m_"):
                                meta[k[4:]] = v
                                to_remove.append(k)
                        for k in to_remove:
                            str_fields.pop(k, None)
                        # 兼容旧格式: 解析 __meta（JSON 字符串）: 消费侧不再做强校验，仅作为原始字符串透传
                        if not meta:
                            meta_raw = str_fields.pop("__meta", None)
                            if meta_raw:
                                meta = {"raw": meta_raw}
                        # 方案A对称：优先取单字段 'payload' 的值作为 payload
                        if "payload" in str_fields:
                            payload_str = str_fields.pop("payload")
                        else:
                            payload_str = json.dumps(str_fields) if str_fields else ""
                    else:
                        payload_str = ""
                        meta = {}
                    # 解码 msg_key 为 str
                    m_key = msg_key.decode('utf-8') if isinstance(msg_key, bytes) else msg_key
                    # 创建StreamMsg对象
                    msg = StreamMsg(payload=payload_str, meta=meta)
                    try:
                        should_ack = callback(m_key, msg)
                        if should_ack:
                            self.redis.xack(self.stream, group, msg_key)
                        elif discard_on_failure:
                            self.redis.xack(self.stream, group, msg_key)  # 直接确认并丢弃
                    except Exception as e: # 出错时根据discard_on_failure参数决定是否确认消息
                        print(f"Error processing message {m_key} from stream {self.stream}: {e}")
                        if discard_on_failure:
                            self.redis.xack(self.stream, group, msg_key)  # 直接确认并丢弃
                        continue