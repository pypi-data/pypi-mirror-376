import os
import time
import uuid
import math
import pytest

from agent_redis_framework import RedisHashClient, get_redis

# UV_INDEX_URL=https://pypi.org/simple/ uv run pytest -q -rs tests/test_hash_client.py

@pytest.fixture(scope="module")
def redis_available():
    """检查 Redis 是否可用，不可用则跳过整个模块测试。"""
    client = get_redis()
    try:
        if not client.ping():
            pytest.skip("Redis server not responding to PING")
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    return client


@pytest.fixture()
def hash_client(redis_available):
    return RedisHashClient(redis_client=redis_available)


def _k(suffix: str = "") -> str:
    return f"test:hash:{uuid.uuid4().hex}{":" + suffix if suffix else ''}"


def test_set_get_types(hash_client: RedisHashClient):
    k = _k("types")
    # str
    assert hash_client.set(k, "s", "hello") in (0, 1)
    assert hash_client.get(k, "s") == "hello"
    # bytes
    assert hash_client.set(k, "b", b"abc") in (0, 1)
    assert hash_client.get(k, "b") == "abc"
    # int
    assert hash_client.set(k, "i", 123) in (0, 1)
    assert hash_client.get(k, "i") == "123"
    # float
    assert hash_client.set(k, "f", 3.14) in (0, 1)
    assert hash_client.get(k, "f") == "3.14"
    # cleanup
    hash_client.clear(k)


def test_setnx_behavior(hash_client: RedisHashClient):
    k = _k("setnx")
    assert hash_client.setnx(k, "a", "1") is True
    # 第二次不应覆盖
    assert hash_client.setnx(k, "a", "2") is False
    assert hash_client.get(k, "a") == "1"
    hash_client.clear(k)


def test_set_many_get_many(hash_client: RedisHashClient):
    k = _k("many")
    mapping = {"a": "x", "b": 2, "c": 3.5, "d": b"zz"}
    hash_client.set_many(k, mapping)
    result = hash_client.get_many(k, mapping.keys())
    assert result == {"a": "x", "b": "2", "c": "3.5", "d": "zz"}
    hash_client.clear(k)


def test_get_all_keys_values_len(hash_client: RedisHashClient):
    k = _k("all")
    hash_client.set_many(k, {"a": "1", "b": "2", "c": "3"})
    assert hash_client.len(k) == 3
    keys = sorted(hash_client.keys(k))
    values = sorted(hash_client.values(k))
    assert keys == ["a", "b", "c"]
    assert sorted(values) == ["1", "2", "3"]
    all_map = hash_client.get_all(k)
    assert all_map == {"a": "1", "b": "2", "c": "3"}
    hash_client.clear(k)


def test_strlen(hash_client: RedisHashClient):
    k = _k("strlen")
    ascii_val = "abc"
    zh_val = "中文"  # utf-8 下每个中文 3 字节，共 6
    hash_client.set(k, "a", ascii_val)
    hash_client.set(k, "z", zh_val)
    assert hash_client.strlen(k, "a") == len(ascii_val.encode("utf-8"))
    assert hash_client.strlen(k, "z") == len(zh_val.encode("utf-8"))
    hash_client.clear(k)


def test_incr_and_incr_float(hash_client: RedisHashClient):
    k = _k("incr")
    # 整数增减（初始不存在等同于 0）
    assert hash_client.incr(k, "i", 5) == 5
    assert hash_client.incr(k, "i", -2) == 3
    # 浮点增量
    f = hash_client.incr_float(k, "f", 1.5)
    assert math.isclose(f, 1.5, rel_tol=1e-9, abs_tol=1e-9)
    f2 = hash_client.incr_float(k, "f", 0.25)
    assert math.isclose(f2, 1.75, rel_tol=1e-9, abs_tol=1e-9)
    hash_client.clear(k)


def test_exists_delete_clear(hash_client: RedisHashClient):
    k = _k("del")
    hash_client.set(k, "x", "1")
    assert hash_client.exists(k, "x") is True
    assert hash_client.delete(k, "x") == 1
    assert hash_client.exists(k, "x") is False
    # 重新设置几个字段，然后 clear
    hash_client.set_many(k, {"a": "1", "b": "2"})
    hash_client.clear(k)
    # 清空后 len 应为 0
    assert hash_client.len(k) == 0


def test_mclear_and_expire(hash_client: RedisHashClient, redis_available):
    k1 = _k("mc1")
    k2 = _k("mc2")
    hash_client.set_many(k1, {"a": "1"})
    hash_client.set_many(k2, {"b": "2"})

    # mclear
    deleted = hash_client.mclear([k1, k2])
    assert deleted >= 2  # 在某些 Redis 版本/场景下，delete 返回删除键数量
    assert redis_available.exists(k1) == 0
    assert redis_available.exists(k2) == 0

    # expire
    k3 = _k("exp")
    hash_client.set(k3, "x", "1")
    assert hash_client.expire(k3, 5) is True
    ttl = redis_available.ttl(k3)
    # ttl 可能略小于 5，这里仅判断 > 0
    assert ttl > 0
    time.sleep(1)
    ttl2 = redis_available.ttl(k3)
    assert ttl2 == -2 or ttl2 <= ttl  # -2 表示键不存在；否则应减少
    hash_client.clear(k3)