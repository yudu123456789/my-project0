import time
import asyncio
from redis.asyncio import Redis

TOKEN_BUCKET_LUA = """
local key_tokens = KEYS[1]
local key_ts = KEYS[2]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local last_tokens = tonumber(redis.call('get', key_tokens) or capacity)
local last_ts = tonumber(redis.call('get', key_ts) or now)

local delta = math.max(0, now - last_ts)
local current_tokens = math.min(capacity, last_tokens + (delta * rate))

if current_tokens >= requested then
    redis.call('set', key_tokens, current_tokens - requested)
    redis.call('set', key_ts, now)
    return 1
else
    return 0
end
"""

class DistributedRateLimiter:
    def __init__(self, redis_conn: Redis, capacity: int, rate: float, prefix: str):
        self.redis = redis_conn
        self.capacity = capacity
        self.rate = rate  # 每秒恢复速率
        self.prefix = prefix
        self._script = self.redis.register_script(TOKEN_BUCKET_LUA)

    async def acquire(self, tokens: int = 1):
        """自旋获取令牌"""
        while True:
            # 修正后的调用逻辑
            res = await self._script(
                keys=[f"{self.prefix}:tokens", f"{self.prefix}:ts"],
                args=[self.capacity, self.rate, tokens, time.time()]
            )
            if res == 1: 
                return True
            await asyncio.sleep(0.1)