from pydantic import BaseModel, Field
from typing import List, Optional
from .enums import TaskStatus

class RawDoc(BaseModel):
    """原始语料模型"""
    id: Optional[int] = None
    content: str
    source: str
    metadata: dict = Field(default_factory=dict)

class FactSheet(BaseModel):
    """Miner 提取的事实清单"""
    is_valid: bool = Field(description="是否包含有效事实")
    facts: List[str] = Field(default_factory=list, description="提取的原子事实列表")
    language: str = "zh"

class QAPair(BaseModel):
    """单条问答对"""
    instruction: str
    response: str

class SFTDataGroup(BaseModel):
    """Synthesizer 生成的指令组"""
    qa_list: List[QAPair]
    category: str  # 逻辑推理, 知识问答, 拒答等

class JudgeResult(BaseModel):
    """Judge 打分结果"""
    score: int = Field(ge=1, le=10)
    reasoning: str
    is_passed: bool
