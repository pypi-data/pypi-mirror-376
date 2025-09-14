from fastapi import FastAPI, HTTPException
from typing import Any
import time
import threading
from contextlib import asynccontextmanager

from agent_redis_framework.sortedset.sorted_queue import SortedSetQueue, SortedTask
from agent_redis_framework.streams.stream_client import StreamClient, StreamMsg

# Stream consumer configuration
STREAM_NAME = "test-stream"

# Global instances
sorted_queue = SortedSetQueue("default-queue")  # 需要传入队列名称
stream_client = StreamClient(STREAM_NAME)  # 需要传入流名称

# Storage for processed data
processed_tasks: list[dict[str, Any]] = []
# 存储消费过的流消息，包含 msg_key 与时间戳，方便测试查询
stream_messages: list[dict[str, Any]] = []
GROUP_NAME = "test-group"
CONSUMER_NAME = "test-consumer"
consumer_thread = None
stop_consumer = threading.Event()


def stream_message_handler(msg_key: str, msg: StreamMsg) -> bool:
    """处理流消息的回调函数"""
    stream_messages.append({
        "stream": STREAM_NAME,  # StreamMsg 不再包含 stream 字段
        "msg_key": msg_key,
        "payload": msg.payload,
        "meta": msg.meta,
        "processed_at": time.time(),
    })
    print(f"收到流消息: {msg_key} @{STREAM_NAME} -> {msg.payload} -> {msg.meta}")
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
    description="简化的API用于测试SortedSetQueue和StreamClient",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/queue/push")
async def queue_push(task: SortedTask, score: float | None = None):
    """推送任务到队列，直接接收 SortedTask（payload 为字符串），可选 score 作为查询参数"""
    try:
        s = score or time.time()
        sorted_queue.push(task, s)
        return {
            "ok": True,
            "message": f"Task pushed to queue",
            "queue": "default-queue",
            "score": s,
            "task": {"payload": task.payload, "meta": task.meta},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/queue/pop")
async def queue_pop(count: int = 1):
    """从队列弹出并处理任务，返回已弹出任务列表"""
    try:
        processed_count = 0
        
        def task_handler(score: float, task: SortedTask) -> bool:
            nonlocal processed_count
            processed_tasks.append({
                "payload": task.payload,
                "meta": task.meta,
                "score": score,
                "processed_at": time.time()
            })
            processed_count += 1
            return True
        
        sorted_queue.pop_and_handle(
            task_handler, count=count
        )
        
        return {
            "processed_count": processed_count,
            "tasks": processed_tasks[-processed_count:] if processed_count > 0 else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/getall")
async def queue_getall():
    """获取所有处理过的任务"""
    return {
        "count": len(processed_tasks),
        "tasks": processed_tasks
    }


@app.post("/stream/push")
async def stream_push(message_request: StreamMsg, maxlen: int | None = None):
    try:
        # StreamMsg 不再包含 stream 字段，直接使用传入的消息
        msg_key = stream_client.push(message_request, maxlen=maxlen)
        return {
            "stream": STREAM_NAME,
            "msg_key": msg_key,
            "payload": message_request.payload,
            "meta": message_request.meta,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stream/messages")
async def get_stream_messages():
    try:
        return {"messages": stream_messages}
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