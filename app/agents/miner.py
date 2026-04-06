from app.domain.schemas import FactSheet
from app.domain.enums import AgentRole
from .base_agent import BaseAgent

class MinerAgent(BaseAgent):
    SYSTEM_PROMPT = """你是一个极其严苛的数据审计师。
    任务：从原始网页/文档中提取客观事实，去除所有广告、无关废话和主观评论。
    规则：
    1. 若内容无意义，将 is_valid 设为 false。
    2. 将复杂段落拆解为简短、原子化的事实陈述。"""

    async def extract(self, raw_text: str) -> FactSheet:
        return await self.call_llm(
            AgentRole.MINER, 
            raw_text, 
            FactSheet, 
            self.SYSTEM_PROMPT
        )
