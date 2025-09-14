from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from typing import Callable, cast, Any

import redis
from ..redis_client import get_redis


@dataclass(frozen=True)
class SortedTask:
    """任务数据类
    
    用于表示队列中的任务，包含任务ID、负载数据和元数据。
    使用frozen=True确保任务对象不可变，保证线程安全。
    
    Attributes:
        id: 任务的唯一标识符
        payload: 任务的负载数据，可以是JSON字符串或原生字符串
        meta: 任务的元数据，用于存储额外的信息如创建时间、优先级等。
              类型与 StreamMsg.meta 保持一致：dict[str, bytes | str | int | float]
    """
    payload: str
    meta: dict[str, bytes | str | int | float] = field(default_factory=dict)

    def to_json(self) -> str:
        """将任务对象序列化为JSON字符串
        
        Returns:
            str: 紧凑格式的JSON字符串，用于存储到Redis中
        """
        return json.dumps(asdict(self), separators=(",", ":"))

    @staticmethod
    def from_json(data: str) -> "SortedTask":
        """从JSON字符串反序列化为任务对象
        
        Args:
            data: JSON格式的任务数据字符串
            
        Returns:
            SortedTask: 反序列化后的任务对象
        """
        obj = json.loads(data)
        return SortedTask(payload=obj.get("payload", ""), meta=obj.get("meta", {}))


class SortedSetQueue:
    """基于Redis有序集合的任务调度队列
    
    这是一个轻量级的Redis有序集合封装，用于任务调度和优先级队列。
    
    主要功能：
    - zadd: 推送带有分数的任务（如优先级或时间戳）
    - zrange: 按分数顺序读取任务
    - zrem: 处理后移除任务
    
    在多消费者场景中，使用ZPOPMIN进行原子性任务声明，
    它会原子性地弹出分数最低的成员。
    
    适用场景：
    - 优先级任务队列
    - 延时任务调度
    - 多消费者任务分发
    
    重构说明：
    - key参数已从构造函数移到各个方法中
    - 一个SortedSetQueue实例可以操作多个不同的sortedset
    - 避免了为每个sortedset创建单独实例的开销
    """

    def __init__(self, key: str) -> None:
        """初始化有序集合队列
        
        Args:            
            key: Redis中有序集合的键名
            redis_client: Redis客户端实例，如果未提供则使用默认客户端
        """
        self.key = key;
        self.redis: redis.Redis = get_redis()

    def push(self, task: SortedTask, score: float | None = None) -> None:
        """将任务推送到队列中
        
        Args:
            task: 要推送的任务对象
            score: 任务的分数（用于排序，分数越低优先级越高）。
                  如果不提供，则使用当前时间戳作为分数
        """
        if score is None:
            score = time.time()
        self.redis.zadd(self.key, {task.to_json(): score})

    def pop_and_handle(
        self,
        callback: Callable[[float, SortedTask], bool],
        *,
        on_failure: Callable[[float, SortedTask], None] | None = None,
        ascending: bool = True,
        count: int = 1,
    ):
        """原子性地弹出并处理任务
        
        按指定的排序顺序，原子性地弹出指定数量的任务并立即处理。
        根据处理函数的返回值决定任务的后续处理：
        - 返回True：任务处理成功，从队列中移除
        - 返回False：任务处理失败，调用失败回调函数或直接丢弃
        
        Args:
            callback: 任务处理函数，接收 (score: float, task: SortedTask) 作为参数，返回bool值表示处理结果
            count: 要弹出的任务数量，默认为1
            on_failure: 可选的失败处理回调函数，接收 (score: float, task: SortedTask)
                       如果未提供，则使用默认行为（直接丢弃失败的任务）
            ascending: 排序顺序控制，默认为True
                      - True: 按分数从低到高的顺序弹出（使用zpopmin）
                      - False: 按分数从高到低的顺序弹出（使用zpopmax）
            
        Returns:
            list[SortedTask]: 已成功处理并移除的任务列表，用于观察和测试
        """
        for _ in range(max(1, count)):
            # 根据排序参数选择弹出方法
            # ascending=True时使用zpopmin从分数最小的开始弹出
            # ascending=False时使用zpopmax从分数最大的开始弹出
            if ascending:
                result = cast(list[tuple[bytes, float]], self.redis.zpopmin(self.key, 1))  # 分数从低到高
            else:
                result = cast(list[tuple[bytes, float]], self.redis.zpopmax(self.key, 1))  # 分数从高到低
            
            # 如果队列为空，没有任务可弹出，则退出循环
            if not result:
                break

            # 解析弹出的任务数据
            # result[0]包含(member, score)元组，member是任务的JSON字符串，score是优先级分数
            member, score = result[0]
            # 将JSON字符串反序列化为SortedTask对象
            # 处理member可能是bytes或str的情况
            task = SortedTask.from_json(member.decode() if isinstance(member, bytes) else member)
            
            # 调用用户提供的处理函数并根据返回值决定后续操作
            fscore = float(score)  # 确保分数为float类型
            success = callback(fscore, task)  # 执行任务处理回调函数
            
            # 如果任务处理失败且提供了失败处理回调函数
            if not success and on_failure is not None:
                # 调用失败处理回调函数，让用户自定义失败处理逻辑
                # 比如重新入队、记录日志、发送告警等
                on_failure(fscore, task)
            # 默认行为：如果没有提供失败处理回调或任务处理成功，则直接丢弃任务

    def size(self, key: str) -> int:
        """获取队列中任务的数量
        
        Args:
            key: Redis中有序集合的键名
            
        Returns:
            int: 队列中任务的总数
        """
        return int(cast(int, self.redis.zcard(key)))

    def clear(self, key: str) -> None:
        """清空队列中的所有任务
        
        Args:
            key: Redis中有序集合的键名
            
        注意：此操作会删除整个Redis键，不可恢复
        """
        self.redis.delete(key)