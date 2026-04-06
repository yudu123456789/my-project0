import asyncio
import json
import time
from app.storage.database import DatabaseManager, SFTTask
from app.core.domain.schemas import RawTask
from loguru import logger

async def import_corpus(file_path: str, batch_size: int = 2000):
    db_mgr = DatabaseManager("postgresql+asyncpg://user:pass@localhost/sft_forge")
    await db_mgr.init_models()
    
    start_time = time.time()
    count = 0
    tasks_buffer = []

    logger.info(f"开始从 {file_path} 导入语料...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                # 预验证数据格式
                task = SFTTask(
                    raw_content=data['content'],
                    source=data.get('source', 'default_import'),
                    metadata=data.get('metadata', {})
                )
                tasks_buffer.append(task)
                count += 1

                # 达到批次大小后执行 Bulk Insert
                if len(tasks_buffer) >= batch_size:
                    async with db_mgr.session_factory() as session:
                        session.add_all(tasks_buffer)
                        await session.commit()
                    tasks_buffer = []
                    logger.info(f"已导入 {count} 条记录...")
            except Exception as e:
                logger.error(f"解析失败: {e}")

    # 处理剩余数据
    if tasks_buffer:
        async with db_mgr.session_factory() as session:
            session.add_all(tasks_buffer)
            await session.commit()

    logger.success(f"导入完成！总计: {count}条, 耗时: {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    # 使用示例: python scripts/import_corpus.py --file corpus.jsonl
    asyncio.run(import_corpus("corpus.jsonl"))