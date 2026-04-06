import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sentence_transformers import SentenceTransformer

from app.core.scheduler import SFTWorkflowScheduler
from app.core.infra.async_pool import AsyncWorkerPool
from app.core.infra.llm_router import LLMRouter
from app.storage.database import DatabaseManager
from app.storage.repository import SFTRepository
from app.agents.miner import MinerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.agents.judge import JudgeAgent
from app.agents.consensus import ConsensusManager
from app.safety.guard import SafetyGuard
from app.indexing.vector_store import SemanticDeDuplicator

load_dotenv()

async def main():
    logger.info("🚀 正在初始化 Agent-SFT-Forge V2.0 生产环境...")

    # 1. 初始化本地 Embedding 模型 (维度 384)
    # 第一次运行会自动下载模型，建议提前下载至本地目录
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    logger.success("Embedding 模型加载成功")

    # 2. 基础设施连接
    db_mgr = DatabaseManager(os.getenv("DATABASE_URL"))
    await db_mgr.init_models()
    redis_conn = Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("BASE_URL"))

    # 3. 核心组件装配
    router = LLMRouter({
        "EXPERT_MODEL": os.getenv("EXPERT_MODEL", "gpt-4"),
        "CHEAP_MODEL": os.getenv("CHEAP_MODEL", "gpt-4o-mini")
    })
    pool = AsyncWorkerPool(max_concurrency=int(os.getenv("MAX_CONCURRENCY", 10)))
    repo = SFTRepository(db_mgr.session_factory)
    safety = SafetyGuard()
    deduplicator = SemanticDeDuplicator(index_path="data/production_v2.index")

    # 4. 智能体装配 (异构共识)
    miner = MinerAgent(openai_client, router)
    synthesizer = SynthesizerAgent(openai_client, router)
    judge_a = JudgeAgent(openai_client, router) 
    judge_b = JudgeAgent(openai_client, router) # 生产建议在 router 中切换不同底座
    consensus = ConsensusManager(judge_a, judge_b)

    # 5. 启动调度器 (注入核心算子)
    scheduler = SFTWorkflowScheduler(
        repo=repo,
        deduplicator=deduplicator,
        safety_guard=safety,
        miner=miner,
        synthesizer=synthesizer,
        consensus=consensus,
        pool=pool,
        router=router,
        embedder=embedder # 注入模型
    )

    try:
        await scheduler.run()
    except Exception as e:
        logger.exception(f"生产线发生致命异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())