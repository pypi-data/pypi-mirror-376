# Agent Redis Framework 测试 API

这是一个基于 FastAPI 的 RESTful API，用于测试 `agent_redis_framework` 中的 `SortedSetQueue` 和 `StreamClient` 功能。

## 项目特性

- **SortedSetQueue**: 基于 Redis 有序集合的轻量任务队列，支持优先级调度和原子弹出处理
- **StreamClient**: 基于 Redis Streams 的消费组封装，支持消息推送、组内消费和自动 ACK
- **FastAPI 测试接口**: 提供完整的 REST API 用于测试和演示框架功能
- **自动流消费**: 服务启动时自动开始消费指定流的消息

## 环境要求

- Python 3.12+
- Redis 服务器 (需要配置 `.env` 文件中的连接信息)
- UV 包管理器

## 启动服务

### 1. 安装依赖

```bash
# 安装开发依赖
UV_INDEX_URL=https://pypi.org/simple/ uv sync --extra dev
```

### 2. 配置 Redis 连接

确保项目根目录的 `.env` 文件包含正确的 Redis 连接信息：

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password
```

### 3. 启动测试服务

```bash
# 使用 uv 运行
UV_INDEX_URL=https://pypi.org/simple/ uv run uvicorn tests.test_serve:app --host 0.0.0.0 --port 8081
```

服务启动后，可以访问：
- **API 文档**: http://localhost:8081/docs
- **健康检查**: http://localhost:8081/health
- **交互式 API 文档**: http://localhost:8081/redoc

## API 端点说明

说明：为简化演示，请求体直接使用框架的原生数据结构。
- 队列相关接口直接接收 `SortedTask`（字段：`payload: str`, `meta: dict`）
- 流相关接口直接接收 `StreamMsg`（字段：`payload: str`, `meta: dict`），流名称由服务端配置

### 健康检查

- `GET /health` - 服务健康状态检查

### 队列操作 (SortedSetQueue)

- `POST /queue/push` - 推送任务到队列（请求体：SortedTask，Query: 可选 `score`）
- `POST /queue/pop` - 从队列弹出并处理任务（返回 processed_count 与 tasks 列表）
- `GET /queue/getall` - 获取所有已处理的任务（返回 count 与 tasks）

### 流操作 (StreamClient)

- `POST /stream/push` - 推送消息到流（请求体：StreamMsg，Query: 可选 `maxlen`）
- `GET /stream/messages` - 获取所有已处理的流消息

## 测试示例

### SortedSetQueue 测试

提示：`SortedTask.payload` 为字符串。若要传递结构化数据，请将其序列化为 JSON 字符串。

#### 1. 推送任务到队列

```bash
# 推送高优先级任务 (score 越小优先级越高)
curl -X POST "http://localhost:8081/queue/push?score=1.0" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"type\":\"email\",\"recipient\":\"user@example.com\",\"priority\":\"high\"}",
    "meta": {"source": "tests/TEST.md"}
  }'

# 推送普通任务
curl -X POST "http://localhost:8081/queue/push?score=5.0" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"type\":\"notification\",\"message\":\"Welcome to our service\"}",
    "meta": {"source": "tests/TEST.md"}
  }'

# 推送延时任务 (使用未来时间戳)
curl -X POST "http://localhost:8081/queue/push?score=1703127056" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"type\":\"reminder\",\"content\":\"Meeting in 1 hour\"}",
    "meta": {"source": "tests/TEST.md"}
  }'
```

#### 2. 弹出并处理任务

```bash
# 弹出 1 个任务 (按 score 升序)
curl -X POST "http://localhost:8081/queue/pop?count=1"

# 弹出多个任务
curl -X POST "http://localhost:8081/queue/pop?count=3"
```

响应示例:
```json
{
  "processed_count": 1,
  "tasks": [
    {
      "payload": "{\"type\":\"email\",\"recipient\":\"user@example.com\",\"priority\":\"high\"}",
      "meta": {"source": "tests/TEST.md"}
    }
  ]
}
```

#### 3. 查看所有处理过的任务

```bash
curl -s "http://localhost:8081/queue/getall"
```

响应示例:
```json
{
  "count": 3,
  "tasks": [
    {"payload": "...", "meta": {}, "score": 1.0, "processed_at": 1703123456.789},
    {"payload": "...", "meta": {}, "score": 1703127056, "processed_at": 1703123457.100}
  ]
}
```

### RedisStreams 测试

#### 1. 推送消息到流

服务启动时会自动开始消费 `test-stream` 流，所以推送到该流的消息会被自动处理。

```bash
# 推送事件消息（payload 为 JSON 字符串）
curl -X POST "http://localhost:8081/stream/push?maxlen=1000" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"event\":\"user_login\",\"user_id\":\"12345\",\"timestamp\":\"2024-01-01T10:00:00Z\",\"ip_address\":\"192.168.1.100\"}",
    "meta": {
      "source": "tests/TEST.md",
      "request_id": "req-123",
      "tags": "login,web"
    }
  }'

# 推送业务数据（payload 为 JSON 字符串）
curl -X POST "http://localhost:8081/stream/push" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "{\"event\":\"order_created\",\"order_id\":\"ORD-001\",\"amount\": 99.99,\"currency\":\"USD\"}",
    "meta": {
      "source": "tests/TEST.md",
      "request_id": "req-456",
      "priority": "normal"
    }
  }'
```

响应示例:
```json
{
  "stream": "test-stream",
  "msg_key": "1703123456789-0",
  "payload": "{\"event\":\"order_created\",\"order_id\":\"ORD-001\",\"amount\": 99.99,\"currency\":\"USD\"}",
  "meta": {
    "source": "tests/TEST.md",
    "request_id": "req-456",
    "priority": "normal"
  }
}
```

#### 2. 查看处理过的流消息

```bash
curl -s "http://localhost:8081/stream/messages"
```

响应示例:
```json
{
  "messages": [
    {
      "stream": "test-stream",
      "msg_key": "1703123456789-0",
      "payload": "{\"event\":\"user_login\",\"user_id\":\"12345\",\"timestamp\":\"2024-01-01T10:00:00Z\",\"ip_address\":\"192.168.1.100\"}",
      "meta": {
        "source": "tests/TEST.md",
        "request_id": "req-123",
        "tags": "login,web"
      },
      "processed_at": 1703123456.789
    }
  ]
}
```

## 完整测试流程

以下是一个完整的测试流程，演示框架的主要功能：

```bash
#!/bin/bash

# 1. 健康检查
echo "=== 健康检查 ==="
curl -s http://localhost:8081/health | jq

# 2. 测试队列功能
echo "\n=== 队列测试 ==="

# 推送多个任务
curl -X POST "http://localhost:8081/queue/push?score=3.0" \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"data\":\"test1\"}", "meta": {}}'

curl -X POST "http://localhost:8081/queue/push?score=1.0" \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"data\":\"test2\"}", "meta": {}}'

curl -X POST "http://localhost:8081/queue/push?score=2.0" \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"data\":\"test3\"}", "meta": {}}'

# 弹出任务 (应该按 score 升序: test2, test3, test1)
curl -X POST "http://localhost:8081/queue/pop?count=2" | jq

# 查看处理结果
curl -s "http://localhost:8081/queue/getall" | jq

# 3. 测试流功能
echo "\n=== 流测试 ==="

# 推送流消息
curl -X POST "http://localhost:8081/stream/push" \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"event\": \"test\", \"data\": \"hello world\"}", "meta": {"source": "tests/TEST.md", "seq": 1}}'

# 等待消息被处理
sleep 2

# 查看处理结果
curl -s "http://localhost:8081/stream/messages" | jq
```

## 故障排除

### 常见问题

1. **Redis 连接失败**
   - 检查 `.env` 文件中的 Redis 配置
   - 确保 Redis 服务器正在运行
   - 验证网络连接和防火墙设置

2. **流消费者认证错误**
   - 检查 Redis 密码配置
   - 确认 Redis 用户权限

3. **端口占用**
   - 更改启动命令中的端口号
   - 检查其他服务是否占用 8081 端口

### 调试模式

启动时添加调试参数：

```bash
UV_INDEX_URL=https://pypi.org/simple/ uv run uvicorn tests.test_serve:app --host 0.0.0.0 --port 8081 --reload --log-level debug
```