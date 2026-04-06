import asyncio
from loguru import logger

class AsyncWorkerPool:
    """有界异步池：通过信号量控制常驻内存(RSS)，防止千万级并发时内存崩溃"""
    def __init__(self, max_concurrency: int):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def run_task(self, coro, task_id):
        async with self.semaphore:
            try:
                return await coro
            except Exception as e:
                logger.error(f"任务 {task_id} 执行异常: {e}")
                return None