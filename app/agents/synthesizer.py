from app.domain.schemas import SFTDataGroup, FactSheet
from app.domain.enums import AgentRole
from .base_agent import BaseAgent

class SynthesizerAgent(BaseAgent):
    SYSTEM_PROMPT = """你是一个顶级 SFT 语料架构师。
    任务：基于提供的事实清单，生成 3 组高质量的问答对。
    要求：
    1. 涵盖不同视角：直接询问、逻辑推理、反事实假设。
    2. 确保回答完全忠实于事实，严禁幻觉。"""

    async def generate(self, facts: FactSheet) -> SFTDataGroup:
        content = "\n".join(facts.facts)
        return await self.call_llm(
            AgentRole.SYNTHESIZER, 
            content, 
            SFTDataGroup, 
            self.SYSTEM_PROMPT
        )
