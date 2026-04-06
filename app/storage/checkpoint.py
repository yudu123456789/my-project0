from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from app.storage.database import SFTTask
from app.core.domain.enums import TaskStatus
from loguru import logger

class CheckpointManager:
    """基于 WAL 逻辑的状态恢复中心"""
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def recover_stale_tasks(self, timeout_minutes: int = 30):
        """
        寻找卡在中间状态（如 MINED, SYNTHESIZING）且超过 30 分钟未更新的任务。
        将它们重置为 PENDING，实现 Exactly-once 处理语义的补偿。
        """
        async with self.session_factory() as session:
            deadline = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            # 找到过期的非终态任务
            stmt = select(SFTTask.id).where(
                and_(
                    SFTTask.status.in_([TaskStatus.MINED, TaskStatus.SYNTHESIZED]),
                    SFTTask.updated_at < deadline
                )
            )
            result = await session.execute(stmt)
            stale_ids = result.scalars().all()

            if not stale_ids:
                logger.info("未发现超时僵尸任务，系统状态健康。")
                return

            # 批量重置状态
            reset_stmt = update(SFTTask).where(SFTTask.id.in_(stale_ids)).values(
                status=TaskStatus.PENDING,
                retry_count=SFTTask.retry_count + 1
            )
            await session.execute(reset_stmt)
            await session.commit()
            logger.warning(f"WAL Checkpoint: 已成功恢复 {len(stale_ids)} 个故障断点任务。")