from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import json
import time
import threading
from contextlib import asynccontextmanager

from agent_redis_framework.sortedset.sorted_queue import SortedSetQueue, Task
from agent_redis_framework.streams.stream_client import RedisStreamsClient, StreamMsg


# Pydantic models for request/response
class TaskRequest(BaseModel):
    id: str
    payload: dict[str, Any]
    score: float | None = None


# 移除原有的 StreamMessageRequest，直接使用 StreamMsg 作为请求体
# class StreamMessageRequest(BaseModel):
#     stream: str
#     fields: dict[str, Any]
#     maxlen: int | None = None


class TaskResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None


# Global instances
sorted_queue = SortedSetQueue()
stream_client = RedisStreamsClient()

# Storage for processed data
processed_tasks: list[dict[str, Any]] = []
# 存储消费过的流消息，包含 msg_key 与时间戳，方便测试查询
stream_messages: list[dict[str, Any]] = []

# Stream consumer configuration
STREAM_NAME = "test-stream"
GROUP_NAME = "test-group"
CONSUMER_NAME = "test-consumer"
consumer_thread = None
stop_consumer = threading.Event()


def stream_message_handler(msg_key: str, msg: StreamMsg) -> bool:
    """处理流消息的回调函数"""
    stream_messages.append({
        "stream": msg.stream,
        "msg_key": msg_key,
        "payload": msg.payload,
        "meta": msg.meta,
        "processed_at": time.time(),
    })
    print(f"收到流消息: {msg_key} @{msg.stream} -> {msg.payload} -> {msg.meta}")
    return True


def start_stream_consumer():
    """启动流消费者"""
    global consumer_thread
    if consumer_thread and consumer_thread.is_alive():
        return
    
    def consumer_worker():
        try:
            # 确保消费者组存在
            stream_client.ensure_group(STREAM_NAME, GROUP_NAME)
            
            # 开始消费
            stream_client.consume(
                streams=[STREAM_NAME],
                group=GROUP_NAME,
                consumer=CONSUMER_NAME,
                callback=stream_message_handler,
                count=10,
                block_ms=1000,
                read_new_only=True,
                discard_on_failure=False
            )
        except Exception as e:
            print(f"流消费者错误: {e}")
    
    consumer_thread = threading.Thread(target=consumer_worker, daemon=True)
    consumer_thread.start()
    print(f"流消费者已启动，监听流: {STREAM_NAME}")


def stop_stream_consumer():
    """停止流消费者"""
    global consumer_thread
    stop_consumer.set()
    if consumer_thread and consumer_thread.is_alive():
        consumer_thread.join(timeout=2)
    print("流消费者已停止")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FastAPI test server for agent-redis-framework")
    start_stream_consumer()
    yield
    # Shutdown
    print("Shutting down FastAPI test server")
    stop_stream_consumer()


app = FastAPI(
    title="Agent Redis Framework Test API",
    description="简化的API用于测试SortedSetQueue和RedisStreamsClient",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/queue/push", response_model=TaskResponse)
async def queue_push(task_request: TaskRequest):
    """推送任务到队列"""
    try:
        payload_str = json.dumps(task_request.payload)
        task = Task(id=task_request.id, payload=payload_str)
        score = task_request.score or time.time()
        sorted_queue.push("default-queue", task, score)
        return TaskResponse(
            success=True,
            message=f"Task {task_request.id} pushed to queue",
            data={"task_id": task_request.id, "score": score}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/queue/pop", response_model=TaskResponse)
async def queue_pop(count: int = 1):
    """从队列弹出任务"""
    try:
        def task_handler(score: float, task: Task) -> bool:
            processed_tasks.append({
                "id": task.id,
                "payload": task.payload,
                "score": score,
                "processed_at": time.time()
            })
            return True
        
        popped_tasks = sorted_queue.pop_and_handle(
            "default-queue", task_handler, count=count
        )
        
        return TaskResponse(
            success=True,
            message=f"Popped {len(popped_tasks)} tasks from queue",
            data={
                "processed_count": len(popped_tasks),
                "tasks": [{"id": task.id, "payload": task.payload} for task in popped_tasks]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/getall", response_model=TaskResponse)
async def queue_getall():
    """获取所有处理过的任务"""
    return TaskResponse(
        success=True,
        message=f"Retrieved {len(processed_tasks)} processed tasks",
        data={"tasks": processed_tasks}
    )


@app.post("/stream/push", response_model=TaskResponse)
async def stream_push(message_request: StreamMsg, maxlen: int | None = None):
    try:
        # 直接透传为 StreamMsg，再交由客户端 push
        msg_to_push = StreamMsg(stream=message_request.stream, payload=message_request.payload, meta=message_request.meta)
        msg_key = stream_client.push(msg_to_push, maxlen=maxlen)
        data = {
            "stream": message_request.stream,
            "msg_key": msg_key,
            "payload": message_request.payload,
            "meta": message_request.meta,
        }
        return TaskResponse(success=True, message=f"Message pushed to stream {message_request.stream}", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stream/messages", response_model=TaskResponse)
async def get_stream_messages():
    try:
        return TaskResponse(success=True, message="OK", data={"messages": stream_messages})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": time.time()}


if __name__ == "__main__":
    # Optionally run the app for manual testing
    try:
        uvicorn = __import__('uvicorn')
        uvicorn.run(app, host="0.0.0.0", port=8081)
    except ImportError:
        print("uvicorn not installed. Install it with: pip install uvicorn")
        print("Or run the server using: uvicorn test_serve:app --host 0.0.0.0 --port 8081")