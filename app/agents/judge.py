from app.domain.schemas import JudgeResult, QAPair
from app.domain.enums import AgentRole
from .base_agent import BaseAgent

class JudgeAgent(BaseAgent):
    SYSTEM_PROMPT = """你是一个毒舌且精准的语料评估员。
    任务：判定问答对是否基于事实且逻辑严密。
    判定准则：
    1. 幻觉检测：回答中出现事实清单以外的信息，直接判定不合格。
    2. 逻辑性：问答是否连贯。
    分数 > 8 且无幻觉才允许通过。"""

    async def evaluate(self, facts: str, qa: QAPair) -> JudgeResult:
        content = f"事实依据：{facts}\n待审问答：Q: {qa.instruction} A: {qa.response}"
        return await self.call_llm(
            AgentRole.JUDGE, 
            content, 
            JudgeResult, 
            self.SYSTEM_PROMPT
        )
