import asyncio
from app.core.domain.enums import AgentRole

class LLMRouter:
    def __init__(self, config):
        self.routes = config
        self.failure_count = 0
        self.failure_threshold = 3  # 连续失败 3 次触发熔断
        self.circuit_open = False
        self.recovery_time = 60     # 熔断后 60s 尝试恢复
        self._lock = asyncio.Lock()

    async def record_failure(self):
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
                logger.error("🚨 熔断触发：OpenAI API 异常，自动降级至本地 vLLM 节点")
                # 开启异步恢复任务
                asyncio.create_task(self._reset_circuit())

    async def record_success(self):
        async with self._lock:
            self.failure_count = 0
            self.circuit_open = False

    async def _reset_circuit(self):
        await asyncio.sleep(self.recovery_time)
        async with self._lock:
            self.failure_count = 0
            self.circuit_open = False
            logger.info("♻️ 熔断尝试恢复：准备重新测试 OpenAI 连通性")

    def get_model(self, role: AgentRole, text: str) -> str:
        # 如果熔断器开启，强制返回本地模型
        if self.circuit_open:
            return self.routes.get("local_fallback", "llama-3-70b-vllm")
        
        # 正常路由逻辑
        if role == AgentRole.MINER and len(text) < 1000:
            return self.routes.get("cheap")
        return self.routes.get("expert")