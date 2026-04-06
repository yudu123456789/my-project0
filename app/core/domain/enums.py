from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "PENDING"           # 初始入库
    EMBEDDED = "EMBEDDED"         # 已计算向量并完成去重
    SKIPPED = "SKIPPED"           # 因语义重复被跳过
    MINED = "MINED"               # 已提取事实
    SYNTHESIZED = "SYNTHESIZED"   # 已合成问答对
    JUDGING = "JUDGING"           # 正在进行共识审计
    PENDING_REVIEW = "REVIEW"     # 审计未通过，等待人工复核
    COMPLETED = "COMPLETED"       # 闭环完成
    FAILED = "FAILED"             # 多次重试后彻底失败

class AgentRole(str, Enum):
    MINER = "miner"
    SYNTHESIZER = "synthesizer"
    JUDGE = "judge"
