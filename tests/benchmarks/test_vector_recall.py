import numpy as np
import pytest
from app.indexing.vector_store import SemanticDeDuplicator

@pytest.mark.asyncio
async def test_ivf_sq8_recall():
    dim = 384
    threshold = 0.92
    engine = SemanticDeDuplicator(dimension=dim, threshold=threshold)
    
    # 1. 模拟 10,000 条背景语料特征
    background_data = np.random.random((10000, dim)).astype('float32')
    # 归一化以适应内积检索
    faiss.normalize_L2(background_data) 
    
    # 训练并灌入索引
    engine.index.train(background_data)
    for vec in background_data:
        await engine.is_duplicate(vec.reshape(1, -1))

    # 2. 构造“已知重复”案例 (给原始向量增加极小噪声)
    original_vec = background_data[0].reshape(1, -1)
    # 增加 0.01 的扰动，相似度应依然 > 0.92
    duplicate_vec = original_vec + np.random.normal(0, 0.01, (1, dim)).astype('float32')
    faiss.normalize_L2(duplicate_vec)

    # 3. 验证召回
    is_dup = await engine.is_duplicate(duplicate_vec)
    
    # 计算实际相似度以辅助判断
    actual_sim = np.dot(original_vec, duplicate_vec.T)
    
    print(f"\n实际相似度: {actual_sim[0][0]:.4f}")
    assert is_dup is True, "IVF-SQ8 漏检了高度相似的语料（召回率异常）"
    logger.success("IVF-SQ8 召回率测试通过：能精准捕捉 0.92 以上的语义重复。")