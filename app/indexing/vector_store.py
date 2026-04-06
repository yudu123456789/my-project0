import faiss
import numpy as np
import os
from loguru import logger

class SemanticDeDuplicator:
    """修正后的本地持久化 FAISS 引擎"""
    def __init__(self, dimension: int = 384, threshold: float = 0.92, index_path: str = "data/production_v2.index"):
        self.dimension = dimension
        self.threshold = threshold
        self.index_path = index_path
        self.is_trained = False
        
        # 初始化基础量化器
        self.quantizer = faiss.IndexFlatIP(dimension)
        # 预设 IVF-SQ8 索引
        self.index = faiss.IndexIVFScalarQuantizer(
            self.quantizer, dimension, 1024, faiss.ScalarQuantizer.QT_8bit
        )
        
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                self.is_trained = True
                logger.info(f"向量库已加载: {self.index.ntotal} 条数据")
            except:
                logger.error("索引文件损坏，请重新训练")

    def train_index(self, train_data: np.ndarray):
        """冷启动训练逻辑"""
        faiss.normalize_L2(train_data)
        self.index.train(train_data)
        self.is_trained = True
        self.save_index()

    async def is_duplicate(self, text_embedding: np.ndarray) -> bool:
        """输入向量格式修正"""
        if not self.is_trained:
            raise RuntimeError("向量索引未训练，请先运行 scripts/index_builder.py")

        # 确保输入是 2D array
        vec = text_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(vec)

        if self.index.ntotal == 0:
            self.index.add(vec)
            return False

        D, I = self.index.search(vec, 1)
        if D[0][0] > self.threshold:
            return True
        
        self.index.add(vec)
        return False

    def save_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)