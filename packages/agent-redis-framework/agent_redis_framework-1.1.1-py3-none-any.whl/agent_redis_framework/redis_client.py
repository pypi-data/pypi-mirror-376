from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import hashlib
import threading

import redis  # type: ignore[reportMissingImports]

from .env import env_str, env_opt_str, env_int, env_float_opt, env_bool


# 说明：
# 本模块提供统一的 Redis 客户端工厂，并使用"连接池（ConnectionPool）"来管理连接。
# 与直接实例化 redis.Redis(host=..., port=...) 相比，连接池能在多线程/高并发场景下
# 高效复用连接，避免频繁创建/销毁 TCP 连接导致的性能损耗。

# 读取环境
_DEFAULT_HOST = env_str("REDIS_HOST", "localhost")
_DEFAULT_PORT = env_int("REDIS_PORT", 6379)
_DEFAULT_DB = env_int("REDIS_DB", 0)
_DEFAULT_SSL = env_bool("REDIS_SSL", False)
_DEFAULT_PASSWORD = env_opt_str("REDIS_PASSWORD")
_DEFAULT_USERNAME = env_opt_str("REDIS_USERNAME", "REDIS_USER")
_DEFAULT_SOCKET_TIMEOUT = env_float_opt("REDIS_SOCKET_TIMEOUT")
_DEFAULT_SOCKET_CONNECT_TIMEOUT = env_float_opt("REDIS_SOCKET_CONNECT_TIMEOUT")
_DEFAULT_HEALTH_CHECK_INTERVAL = env_int("REDIS_HEALTH_CHECK_INTERVAL", 0)
_DEFAULT_MAX_CONNECTIONS = env_int("REDIS_MAX_CONNECTIONS", 10)
_DEFAULT_RETRY_ON_TIMEOUT = env_bool("REDIS_RETRY_ON_TIMEOUT", True)


@dataclass(frozen=True)
class RedisConfig:
    """Redis 客户端配置（线程安全，不要打印敏感字段）

    注意：请避免在日志中打印 password 等敏感字段。

    字段含义：
    - host/port/db/username/password/ssl：标准 Redis 连接参数
    - socket_timeout：单次 socket 操作超时时间（秒）
    - socket_connect_timeout：建立连接时的超时时间（秒）
    - health_check_interval：健康检查间隔（秒），0 表示不开启
    - max_connections：连接池的最大连接数（并发能力上限）
    - retry_on_timeout：发生超时时是否进行自动重试（依业务需求选择）
    """

    host: str = _DEFAULT_HOST
    port: int = _DEFAULT_PORT
    db: int = _DEFAULT_DB
    ssl: bool = _DEFAULT_SSL
    password: Optional[str] = _DEFAULT_PASSWORD
    username: Optional[str] = _DEFAULT_USERNAME
    socket_timeout: Optional[float] = _DEFAULT_SOCKET_TIMEOUT
    socket_connect_timeout: Optional[float] = _DEFAULT_SOCKET_CONNECT_TIMEOUT
    health_check_interval: int = _DEFAULT_HEALTH_CHECK_INTERVAL
    max_connections: int = _DEFAULT_MAX_CONNECTIONS
    retry_on_timeout: bool = _DEFAULT_RETRY_ON_TIMEOUT


# 全局连接池缓存，按配置进行复用；配合互斥锁保证并发安全
_pools: dict[tuple, "redis.ConnectionPool"] = {}
_lock = threading.Lock()


def _hash_secret(secret: Optional[str]) -> str:
    """对敏感字段做不可逆哈希，仅用于区分不同配置的连接池。

    不会打印明文，也不会暴露在日志里。
    """
    if not secret:
        return ""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _pool_key(cfg: RedisConfig) -> tuple:
    """根据配置生成连接池缓存键（不包含明文密码）。"""
    return (
        cfg.host,
        cfg.port,
        cfg.db,
        cfg.username,
        _hash_secret(cfg.password),  # 只保存密码哈希用于区分，不记录明文
        cfg.ssl,
        cfg.socket_timeout,
        cfg.socket_connect_timeout,
        cfg.health_check_interval,
        cfg.max_connections,
        cfg.retry_on_timeout,
    )


def get_redis_pool(config: Optional[RedisConfig] = None) -> "redis.ConnectionPool":
    """获取（或创建）Redis 连接池实例。

    - 相同配置将复用同一个连接池，避免重复创建导致资源浪费。
    - 线程安全：内部使用互斥锁保证并发创建时只初始化一次。
    """
    cfg = config or RedisConfig()
    key = _pool_key(cfg)

    # 双重检查 + 互斥保护，避免高并发场景下重复创建连接池
    pool = _pools.get(key)
    if pool is not None:
        return pool

    with _lock:
        pool = _pools.get(key)
        if pool is None:
            # 将配置透传给连接池（底层会将其作为连接创建参数）
            cp_kwargs = {
                "host": cfg.host,
                "port": cfg.port,
                "db": cfg.db,
                "username": cfg.username,
                "password": cfg.password,
                "socket_timeout": cfg.socket_timeout,
                "socket_connect_timeout": cfg.socket_connect_timeout,
                "health_check_interval": cfg.health_check_interval,
                "max_connections": cfg.max_connections,
            }
            if cfg.ssl:
                cp_kwargs["ssl"] = True
            pool = redis.ConnectionPool(**cp_kwargs)
            _pools[key] = pool
        return pool


def get_redis() -> "redis.Redis":
    """创建一个基于连接池的同步 Redis 客户端。

    返回：
    - redis.Redis：已绑定连接池的客户端实例。

    说明：
    - 自动从环境变量加载 Redis 配置，无需手动传参。
    - 上层代码可像原来一样直接使用 redis 命令（xadd、xreadgroup、zadd、zpopmin 等）。
    - 客户端共享底层连接池，天然适配多线程/多协程并发复用连接。
    """
    cfg = RedisConfig()
    pool = get_redis_pool(cfg)
    # 通过连接池创建客户端；decode_responses 等参数已在连接池层面生效
    return redis.Redis(connection_pool=pool, retry_on_timeout=cfg.retry_on_timeout)


# 为了让 mypy/pyright 等类型检查器更友好地识别导出项
__all__ = ["RedisConfig", "get_redis", "get_redis_pool"]