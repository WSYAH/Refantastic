from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from loguru import logger

from config import get_settings


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def initialize(self):
        """初始化向量存储"""
        pass
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档到向量库"""
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """相似度检索"""
        pass
    
    @abstractmethod
    async def keyword_search(
        self,
        keywords: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """关键词检索"""
        pass
    
    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """混合检索（相似度 + 关键词）"""
        pass
    
    @abstractmethod
    async def delete_documents(self, ids: List[str]) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB 向量存储实现"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection = None
        self.embedding_model = None
    
    async def initialize(self):
        """初始化 ChromaDB"""
        logger.info("初始化 ChromaDB 向量存储...")
        self.client = None 
        
        # # 初始化客户端
        # self.client = chromadb.PersistentClient(
        #     path=self.settings.CHROMA_PERSIST_DIR,
        #     settings=ChromaSettings(anonymized_telemetry=False)
        # )
        
        # # 加载嵌入模型
        # self.embedding_model = SentenceTransformer(
        #     self.settings.EMBEDDING_MODEL,
        #     device='cuda' if self._has_cuda() else 'cpu'
        # )
        
        # # 获取或创建集合
        # self.collection = self.client.get_or_create_collection(
        #     name="documents",
        #     metadata={"description": "公文知识库"}
        # )
        
        logger.info("ChromaDB 初始化完成")
    
    def _has_cuda(self) -> bool:
        """检查是否有 CUDA"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档"""
        # if ids is None:
        #     import uuid
        #     ids = [str(uuid.uuid4()) for _ in documents]
        
        # # 生成嵌入向量
        # embeddings = self.embedding_model.encode(
        #     documents,
        #     convert_to_tensor=False,
        #     show_progress_bar=True
        # ).tolist()
        
        # # 添加到 ChromaDB
        # self.collection.add(
        #     embeddings=embeddings,
        #     documents=documents,
        #     metadatas=metadatas,
        #     ids=ids
        # )
        
        # logger.info(f"添加 {len(documents)} 个文档到向量库")
        ids = ["28257"]
        return ids
    
    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """相似度检索"""
        # query_embedding = self.embedding_model.encode(
        #     query,
        #     convert_to_tensor=False
        # ).tolist()
        
        # results = self.collection.query(
        #     query_embeddings=[query_embedding],
        #     n_results=top_k,
        #     where=filter_dict
        # )
        
        # # 格式化结果
        # documents = []
        # for i in range(len(results['ids'][0])):
        #     documents.append({
        #         'id': results['ids'][0][i],
        #         'content': results['documents'][0][i],
        #         'metadata': results['metadatas'][0][i],
        #         'score': 1 - results['distances'][0][i]  # 转换为相似度分数
        #     })
        documents = []
        return documents
    
    async def keyword_search(
        self,
        keywords: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """关键词检索"""
        # ChromaDB 支持全文搜索
        # where_document = {"$or": [{"$contains": kw} for kw in keywords]}
        
        # results = self.collection.query(
        #     query_embeddings=None,
        #     n_results=top_k,
        #     where_document=where_document
        # )
        
        # documents = []
        # for i in range(len(results['ids'][0])):
        #     documents.append({
        #         'id': results['ids'][0][i],
        #         'content': results['documents'][0][i],
        #         'metadata': results['metadatas'][0][i],
        #         'score': 1.0  # 关键词匹配给满分
        #     })
        documents = []
        return documents
    
    async def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """混合检索"""
        # 相似度检索
        sim_results = await self.similarity_search(query, top_k * 2)
        
        # 关键词检索
        kw_results = await self.keyword_search(keywords, top_k * 2)
        
        # 合并和重排序
        combined = {}
        for doc in sim_results:
            combined[doc['id']] = {
                **doc,
                'final_score': doc['score'] * alpha
            }
        
        for doc in kw_results:
            if doc['id'] in combined:
                combined[doc['id']]['final_score'] += doc['score'] * (1 - alpha)
            else:
                combined[doc['id']] = {
                    **doc,
                    'final_score': doc['score'] * (1 - alpha)
                }
        
        # 排序并返回 top_k
        sorted_docs = sorted(
            combined.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )
        
        return sorted_docs[:top_k]
    
    async def delete_documents(self, ids: List[str]) -> bool:
        """删除文档"""
        self.collection.delete(ids=ids)
        logger.info(f"删除 {len(ids)} 个文档")
        return True
    
    async def close(self):
        """关闭连接"""
        # ChromaDB 会自动持久化
        logger.info("ChromaDB 连接关闭")


# 单例模式
_vector_store = None


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        if settings.VECTOR_DB_TYPE == "chromadb":
            _vector_store = ChromaVectorStore()
        else:
            raise ValueError(f"不支持的向量数据库类型: {settings.VECTOR_DB_TYPE}")
    return _vector_store
