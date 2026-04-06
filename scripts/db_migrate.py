import asyncio
import os
from sqlalchemy import text
from app.storage.database import DatabaseManager
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    db_url = os.getenv("DATABASE_URL")
    db_mgr = DatabaseManager(db_url)
    
    logger.info("正在执行数据库 Schema 迁移...")
    
    async with db_mgr.engine.begin() as conn:
        # 1. 创建基础表 (基于 database.py 定义)
        await db_mgr.init_models()
        
        # 2. 强制增加 fingerprint 唯一索引 (如果不存在)
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_sft_tasks_fingerprint 
            ON sft_tasks (fingerprint);
        """))
        
        # 3. 增加状态索引优化扫描性能
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sft_tasks_status 
            ON sft_tasks (status);
        """))

    logger.success("数据库迁移完成：Fingerprint 唯一约束已生效。")

if __name__ == "__main__":
    asyncio.run(migrate())