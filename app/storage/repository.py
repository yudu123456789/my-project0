from sqlalchemy import text
from app.storage.database import SFTTask

class SFTRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def _get_table_name(self, source: str) -> str:
        """根据语料来源动态计算表名"""
        # 生产环境建议根据 source 的 hash 取模分表，或按预定义的业务标签分表
        safe_source = source.lower().replace("-", "_")
        return f"sft_tasks_{safe_source}"

    async def insert_sharded_task(self, source: str, content: str):
        """动态分表插入"""
        table_name = self._get_table_name(source)
        
        # 资深开发者提示：需确保表已存在，可以在脚本启动时预建常用表
        sql = text(f"""
            INSERT INTO {table_name} (raw_content, source, status, created_at)
            VALUES (:content, :source, 'PENDING', NOW())
        """)
        
        async with self.session_factory() as session:
            await session.execute(sql, {"content": content, "source": source})
            await session.commit()