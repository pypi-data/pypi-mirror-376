from __future__ import annotations

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


    def ensure_group(self, group: str) -> None:
        """确保消费者组存在, 如果不存在则创建
        Args:
            group: 消费者组名称
        Note:
            如果消费者组已存在, 会忽略BUSYGROUP错误；
            如果流不存在, 会自动创建流。
        """
        try:
            self.redis.xgroup_create(name=self.stream, groupname=group, id="$", mkstream=True)
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
            for k, v in msg.meta.items():
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
        count: int = 10,
        block_ms: int = 5000,
    ) -> None:
        """消费流消息
        
        Args:
            group: 消费者组名称
            consumer: 消费者名称
            callback: 消息处理函数，返回 True 确认消息，False 不确认
            count: 每次读取的消息数量
            block_ms: 阻塞等待时间（毫秒）
        """
        self.ensure_group(group)
        
        while True:
            try:
                entries = self.redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={self.stream: ">"},
                    count=count,
                    block=block_ms,
                )
            except Exception:
                time.sleep(0.5)
                continue

            if not entries:
                continue

            for _, messages in entries:  # type: ignore
                for msg_key, fields in messages:
                    # 解码字段
                    decoded_fields = {
                        k.decode('utf-8') if isinstance(k, bytes) else k:
                        v.decode('utf-8') if isinstance(v, bytes) else v
                        for k, v in fields.items()
                    }
                    
                    # 提取 payload 和 meta
                    payload = decoded_fields.pop("payload", "")
                    meta = {k[4:]: v for k, v in decoded_fields.items() if k.startswith("__m_")}
                    
                    # 创建消息对象
                    msg_id = msg_key.decode('utf-8') if isinstance(msg_key, bytes) else msg_key
                    msg = StreamMsg(payload=payload, meta=meta)
                    
                    # 处理消息
                    try:
                        if callback(msg_id, msg):
                            self.redis.xack(self.stream, group, msg_key)
                    except Exception as e:
                        print(f"Error processing message {msg_id}: {e}")