from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, JSON, DateTime, func
from datetime import datetime
from app.domain.enums import TaskStatus

class Base(DeclarativeBase):
    pass

class SFTTask(Base):
    """SFT 任务表：核心状态机存储"""
    __tablename__ = "sft_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_content: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String(50))
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING, index=True)
    
    # 结构化中间结果
    mined_facts: Mapped[dict] = mapped_column(JSON, nullable=True)
    qa_pairs: Mapped[dict] = mapped_column(JSON, nullable=True)
    judge_report: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now(), server_default=func.now())

# 异步引擎配置
class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, pool_size=20, max_overflow=10)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_models(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
