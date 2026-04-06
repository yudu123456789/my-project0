import re
import asyncio
from loguru import logger

class SafetyGuard:
    """生产级安全栅栏：PII 脱敏与内容合规扫描"""
    def __init__(self):
        # 敏感信息正则算子
        self.pii_patterns = {
            "PHONE": re.compile(r'1[3-9]\d{9}'),
            "EMAIL": re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        }

    def mask_pii(self, text: str) -> str:
        """PII 脱敏：将手机号/邮箱替换为占位符"""
        for label, pattern in self.pii_patterns.items():
            text = pattern.sub(f"<{label}>", text)
        return text

    async def check_toxicity(self, text: str) -> float:
        """
        毒性过滤逻辑：
        大厂通常对接专用安全模型（如 Llama-Guard 3）。
        此处实现一个基于关键词的快速评分逻辑。
        """
        toxic_keywords = ["暴力", "仇恨", "违禁", "赌博"]
        hits = sum(1 for word in toxic_keywords if word in text)
        score = hits / len(toxic_keywords)
        return min(score, 1.0)