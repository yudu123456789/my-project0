import asyncio
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from app.indexing.vector_store import SemanticDeDuplicator
from loguru import logger

# 建议与 vector_store 中的配置保持一致
INDEX_PATH = "data/production_v2.index"
MODEL_NAME = "all-MiniLM-L6-v2" # 维度 384

async def build_initial_index(corpus_path: str):
    logger.info(f"正在冷启动向量库索引...")
    
    # 1. 初始化本地 Embedding 模型
    model = SentenceTransformer(MODEL_NAME)
    
    # 2. 读取训练样本
    texts = []
    if not os.path.exists(corpus_path):
        logger.error(f"未找到训练语料: {corpus_path}")
        return

    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            texts.append(data.get('content', ''))
            if len(texts) >= 10000: break # 训练集上限
            
    if not texts:
        logger.error("训练语料为空！")
        return

    # 3. 提取特征向量
    logger.info(f"正在为 {len(texts)} 条样本提取特征...")
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    # 4. 执行 IVF 质心训练
    deduplicator = SemanticDeDuplicator(
        dimension=384, 
        index_path=INDEX_PATH
    )
    
    # 强制重新训练
    deduplicator.train_index(embeddings.astype('float32'))
    
    logger.success(f"冷启动完成！索引已保存至 {INDEX_PATH}")
    logger.info("现在可以安全启动 main.py 进行千万级生产了。")

if __name__ == "__main__":
    # 使用示例：python scripts/index_builder.py
    # 假设你已经通过之前的导入脚本准备好了基础语料
    asyncio.run(build_initial_index("data/raw_samples.jsonl"))