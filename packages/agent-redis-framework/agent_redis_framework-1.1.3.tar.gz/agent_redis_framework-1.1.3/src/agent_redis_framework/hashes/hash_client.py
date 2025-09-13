from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..redis_client import get_redis

# 支持的标量类型：与项目中 meta/payload 的风格保持一致（标量优先，复杂结构请先序列化为字符串）
SupportedScalar = bytes | str | int | float


def _to_str(v: SupportedScalar) -> str:
    """将值转换为字符串以便写入 Redis。

    - bytes -> utf-8 解码
    - str   -> 原样返回
    - int/float -> 使用 str() 转换
    """
    if isinstance(v, bytes):
        return v.decode("utf-8")
    if isinstance(v, (int, float)):
        return str(v)
    return v


def _from_bytes(v: bytes | str | None) -> str | None:
    """将从 Redis 读取到的值转换为 str（如果是 bytes 则解码）。"""
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8")
    return v


class RedisHashClient:
    """Redis Hash 数据结构的便捷封装

    提供对常见 Hash 操作的高层封装，统一处理 bytes/str 的转换，确保类型友好：
    - set/get：单字段写入与读取
    - set_many/get_many：多字段批量操作
    - get_all/keys/values/len：便捷查询
    - incr/incr_float：数值自增
    - exists/delete/clear：字段与键的删除
    - iterate_scan：基于 HSCAN 的惰性迭代器

    使用方式：
        >>> from agent_redis_framework import RedisHashClient
        >>> h = RedisHashClient()
        >>> h.set("user:1", "name", "Alice")
        >>> h.get("user:1", "name")
        'Alice'
    """

    def __init__(self, *, redis_client=None) -> None:
        self.redis = redis_client or get_redis()

    # 基础写入
    def set(self, key: str, field: str, value: SupportedScalar) -> int:
        """设置单个字段。
        返回：1 表示新字段，0 表示覆盖。
        """
        return int(self.redis.hset(key, field, _to_str(value)))

    def setnx(self, key: str, field: str, value: SupportedScalar) -> bool:
        """仅当字段不存在时设置，返回 True 表示设置成功。"""
        return bool(self.redis.hsetnx(key, field, _to_str(value)))

    def set_many(self, key: str, mapping: dict[str, SupportedScalar]) -> None:
        """批量设置多个字段。"""
        if not mapping:
            return
        data = {k: _to_str(v) for k, v in mapping.items()}
        # redis-py: hset(name, mapping={...})
        self.redis.hset(key, mapping=data)

    # 基础读取
    def get(self, key: str, field: str) -> str | None:
        """获取单个字段的值；不存在则返回 None。"""
        return _from_bytes(self.redis.hget(key, field))

    def get_many(self, key: str, fields: Iterable[str]) -> dict[str, str | None]:
        """批量获取多个字段，返回字典（保持字段对应的顺序不做强保证）。"""
        fs = list(fields)
        if not fs:
            return {}
        values = self.redis.hmget(key, fs)
        # values: list[bytes|str|None]
        return {f: _from_bytes(v) for f, v in zip(fs, values)}

    def get_all(self, key: str) -> dict[str, str]:
        """获取整个 Hash（字段和值均以 str 返回）。"""
        raw = self.redis.hgetall(key)  # dict[bytes|str, bytes|str]
        out: dict[str, str] = {}
        for k, v in raw.items():
            kk = k.decode("utf-8") if isinstance(k, bytes) else k
            vv = v.decode("utf-8") if isinstance(v, bytes) else v
            out[kk] = vv
        return out

    # 统计与键空间
    def len(self, key: str) -> int:
        """返回字段数量。"""
        return int(self.redis.hlen(key))

    def keys(self, key: str) -> list[str]:
        """返回所有字段名（str）。"""
        raw = self.redis.hkeys(key)
        return [k.decode("utf-8") if isinstance(k, bytes) else k for k in raw]

    def values(self, key: str) -> list[str]:
        """返回所有字段值（str）。"""
        raw = self.redis.hvals(key)
        return [v.decode("utf-8") if isinstance(v, bytes) else v for v in raw]

    def strlen(self, key: str, field: str) -> int:
        """返回字段值的字节长度（基于 Redis HSTRLEN）。"""
        return int(self.redis.hstrlen(key, field))

    # 数值操作
    def incr(self, key: str, field: str, amount: int = 1) -> int:
        """将字段的整数值增加 amount，返回最新值。"""
        return int(self.redis.hincrby(key, field, amount))

    def incr_float(self, key: str, field: str, amount: float = 1.0) -> float:
        """将字段的浮点数值增加 amount，返回最新值。"""
        return float(self.redis.hincrbyfloat(key, field, amount))

    # 字段存在与删除
    def exists(self, key: str, field: str) -> bool:
        """字段是否存在。"""
        return bool(self.redis.hexists(key, field))

    def delete(self, key: str, *fields: str) -> int:
        """删除一个或多个字段，返回删除的字段数量。"""
        if not fields:
            return 0
        return int(self.redis.hdel(key, *fields))

    def clear(self, key: str) -> None:
        """删除整个 Hash 键。"""
        self.redis.delete(key)

    def mclear(self, keys: Iterable[str]) -> int:
        """批量删除多个 Hash 键（底层 DEL），返回成功删除的键数量。"""
        ks = list(keys)
        if not ks:
            return 0
        return int(self.redis.delete(*ks))

    def expire(self, key: str, seconds: int) -> bool:
        """为 Hash 键设置过期时间（秒），返回是否设置成功。"""
        return bool(self.redis.expire(key, seconds))

    # 扫描遍历
    def iterate_scan(self, key: str, match: str | None = None, count: int | None = None) -> Iterator[tuple[str, str]]:
        """基于 HSCAN 的惰性迭代器，逐步返回 (field, value)。

        Args:
            key: Hash 键名
            match: 模式匹配，类似 'prefix:*'
            count: 每次扫描的建议数量（非严格）
        """
        cursor = 0
        while True:
            cursor, data = self.redis.hscan(name=key, cursor=cursor, match=match, count=count)
            if not data:
                if cursor == 0:
                    break
            for k, v in data.items():
                kk = k.decode("utf-8") if isinstance(k, bytes) else k
                vv = v.decode("utf-8") if isinstance(v, bytes) else v
                yield kk, vv
            if cursor == 0:
                break