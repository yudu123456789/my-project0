import asyncio
from loguru import logger
from app.core.domain.enums import TaskStatus
from app.utils.telemetry import telemetry
from openai import OpenAIError

class SFTWorkflowScheduler:
    def __init__(self, repo, deduplicator, safety_guard, miner, synthesizer, consensus, pool, router, embedder):
        self.repo = repo
        self.deduplicator = deduplicator
        self.safety_guard = safety_guard
        self.miner = miner
        self.synthesizer = synthesizer
        self.consensus = consensus
        self.pool = pool
        self.router = router
        self.embedder = embedder # 新增 Embedding 模型注入
        self._stop_event = asyncio.Event()

    async def process_task(self, task):
        """核心生产线：修复了去重阶段的向量提取逻辑"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 1. 语义去重：先提取向量，再比对
            # 使用本地 embedder 提取特征
            embedding = self.embedder.encode([task.raw_content])[0]
            if await self.deduplicator.is_duplicate(embedding):
                await self.repo.update_task_status(task.id, TaskStatus.SKIPPED)
                return

            # 2. 安全脱敏
            safe_content = self.safety_guard.mask_pii(task.raw_content)

            # --- LLM 智能体协同流 ---
            try:
                # 事实提取
                facts = await self.miner.extract(safe_content)
                if not facts.is_valid:
                    await self.repo.update_task_status(task.id, TaskStatus.FAILED)
                    return

                # 指令合成
                qa_group = await self.synthesizer.generate(facts)
                
                # 异构博弈审计
                final_status, report = await self.consensus.audit(facts, qa_group.qa_list)
                
                # 链路成功，重置熔断器
                await self.router.record_success() 
                
            except (OpenAIError, asyncio.TimeoutError) as api_err:
                logger.error(f"LLM 链路抖动: {api_err}")
                await self.router.record_failure()
                raise api_err 

            # 3. 结果落库
            await self.repo.update_task_status(
                task.id, final_status, 
                mined_facts=facts.dict(), 
                qa_pairs=qa_group.dict(),
                judge_report=report
            )
            
            telemetry.record_task(final_status.value.lower())
            
        except Exception as e:
            logger.error(f"任务 {task.id} 流程中断: {e}")
            await self.repo.update_task_status(task.id, TaskStatus.FAILED, retry_count=task.retry_count+1)

    async def run(self):
        logger.info("Agent-SFT-Forge 生产线已拉起...")
        while not self._stop_event.is_set():
            tasks = await self.repo.fetch_pending_tasks(limit=10)
            if not tasks:
                await asyncio.sleep(5)
                continue
            await asyncio.gather(*[self.pool.run_task(self.process_task(t), t.id) for t in tasks])

    def stop(self):
        self._stop_event.set()