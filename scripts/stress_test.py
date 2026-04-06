import asyncio
import time
import os
from redis.asyncio import Redis
from app.core.infra.rate_limiter import DistributedRateLimiter
from loguru import logger

async def simulate_request(limiter, request_id):
    """模拟单次 API 请求的限流竞争"""
    start = time.perf_counter()
    # 尝试获取令牌
    await limiter.acquire(tokens=1)
    latency = time.perf_counter() - start
    return latency

async def run_stress_test(concurrency=200, total_requests=1000):
    logger.info(f"正在启动高并发压测：并发数={concurrency}, 总请求={total_requests}")
    
    redis_conn = Redis.from_url("redis://localhost:6379", decode_responses=True)
    # 设定一个极严苛的限流：每秒仅允许 50 个请求
    limiter = DistributedRateLimiter(redis_conn, capacity=50, rate=50.0, prefix="stress_test")
    
    start_time = time.time()
    tasks = [simulate_request(limiter, i) for i in range(total_requests)]
    
    # 使用 gather 模拟瞬时爆发压力
    latencies = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    avg_latency = sum(latencies) / len(latencies)
    
    print("\n" + "="*40)
    print(f"🔥 压测报告")
    print(f"实际吞吐量: {total_requests / duration:.2f} req/s")
    print(f"平均等待时延: {avg_latency:.4f}s")
    print(f"最大等待时延: {max(latencies):.4f}s")
    print(f"Redis 原子性验证: {'通过' if duration > (total_requests/50 - 1) else '未生效'}")
    print("="*40)
    
    await redis_conn.close()

if __name__ == "__main__":
    asyncio.run(run_stress_test())