import asyncio
from sqlalchemy import text
from app.storage.database import DatabaseManager
from loguru import logger

# 预定义的语料来源，将映射为独立表名
SHARD_SOURCES = ["common_crawl", "wikipedia", "github_issue", "stack_overflow"]

async def init_shards():
    db_mgr = DatabaseManager("postgresql+asyncpg://user:pass@localhost/sft_forge")
    async with db_mgr.engine.begin() as conn:
        for source in SHARD_SOURCES:
            table_name = f"sft_tasks_{source}"
            logger.info(f"正在初始化分表: {table_name}")
            
            # 1. 动态创建表（继承主表结构）
            await conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    LIKE sft_tasks INCLUDING ALL
                );
            """))
            
            # 2. 创建基于内容指纹的唯一索引（保证全局幂等）
            await conn.execute(text(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_fingerprint 
                ON {table_name} (fingerprint);
            """))
            
            # 3. 创建状态索引（加速调度器扫描）
            await conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_status 
                ON {table_name} (status);
            """))

    logger.success("所有分表初始化完成，系统已准备好接收亿级语料。")

if __name__ == "__main__":
    asyncio.run(init_shards())