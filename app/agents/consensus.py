from typing import List
from app.domain.schemas import JudgeResult, QAPair, FactSheet
from app.domain.enums import TaskStatus
from .judge import JudgeAgent
from loguru import logger

class ConsensusManager:
    """异构模型共识决策器：解决 LLM-as-a-Judge 的同质化偏见"""
    def __init__(self, judge_primary: JudgeAgent, judge_secondary: JudgeAgent):
        # 建议在 main.py 装配时：
        # judge_primary 使用 DeepSeek-V3
        # judge_secondary 使用 Llama-3-70B
        self.judge_a = judge_primary
        self.judge_b = judge_secondary
        self.score_variance_threshold = 2.0

    async def audit(self, facts: FactSheet, qa_group: List[QAPair]) -> (TaskStatus, dict):
        """
        对 QA 对进行双重审计。
        返回：(最终状态, 审计报告明细)
        """
        fact_str = "\n".join(facts.facts)
        report_details = []
        is_consensus_failed = False
        
        for idx, qa in enumerate(qa_group):
            # 1. 异构模型同步初审
            res_a = await self.judge_a.evaluate(fact_str, qa)
            res_b = await self.judge_b.evaluate(fact_str, qa)

            # 2. 计算分歧度
            variance = abs(res_a.score - res_b.score)
            
            # 记录本次审计详情供 HITL 展示
            report_details.append({
                "qa_idx": idx,
                "model_a": {"score": res_a.score, "reason": res_a.reasoning},
                "model_b": {"score": res_b.score, "reason": res_b.reasoning},
                "variance": variance
            })

            # 3. 冲突判定逻辑
            # 情况 A: 分数方差过大 (共识失败)
            if variance > self.score_variance_threshold:
                logger.warning(f"QA[{idx}] 触发共识分歧: Delta={variance:.1f}")
                is_consensus_failed = True
            
            # 情况 B: 任意一模型判定不合格 (质量拦截)
            if not (res_a.is_passed and res_b.is_passed):
                logger.info(f"QA[{idx}] 未通过质量门槛")
                is_consensus_failed = True

        # 只要有一组 QA 存在争议，该任务即进入人工复核队列
        if is_consensus_failed:
            return TaskStatus.PENDING_REVIEW, {"audit_log": report_details}
        
        return TaskStatus.COMPLETED, {"audit_log": report_details}