from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from datetime import datetime
import uuid
from loguru import logger

from models.knowledge import KnowledgeDocument, KnowledgeCategory
from models import KnowledgeBase, KnowledgeBaseDocument, Document
from core.vector_store import get_vector_store
from core.database import get_db


class KnowledgeService:
    """知识库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = get_vector_store()
    
    async def create_document(
        self,
        title: str,
        content: str,
        doc_type: str,
        author: Optional[str] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_vectorize: bool = True
    ) -> KnowledgeDocument:
        """
        创建知识库文档
        
        Args:
            title: 标题
            content: 内容
            doc_type: 文档类型
            author: 作者
            department: 部门
            tags: 标签
            keywords: 关键词
            metadata: 额外元数据
            auto_vectorize: 是否自动向量化
        """
        try:
            doc_id = str(uuid.uuid4())
            
            document = KnowledgeDocument(
                id=doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                author=author,
                department=department,
                tags=tags or [],
                keywords=keywords or [],
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # 自动向量化
            if auto_vectorize:
                await self.vectorize_document(doc_id)
            
            logger.info(f"创建知识库文档成功: {doc_id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建知识库文档失败: {str(e)}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """获取文档"""
        try:
            result = await self.db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            )
            document = result.scalar_one_or_none()
            
            # 增加浏览次数
            if document:
                await self._increment_view_count(doc_id)
            
            return document
            
        except Exception as e:
            logger.error(f"获取文档失败: {str(e)}")
            return None
    
    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = "active",
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[List[KnowledgeDocument], int]:
        """
        列出文档
        
        Returns:
            (文档列表, 总数)
        """
        try:
            # 构建查询条件
            conditions = [KnowledgeDocument.status == status]
            
            if doc_type:
                conditions.append(KnowledgeDocument.doc_type == doc_type)
            
            if is_public is not None:
                conditions.append(KnowledgeDocument.is_public == is_public)
            
            if tags:
                # 标签匹配（JSON数组包含）
                for tag in tags:
                    conditions.append(
                        func.json_contains(KnowledgeDocument.tags, f'"{tag}"')
                    )
            
            # 查询总数
            count_query = select(func.count()).select_from(KnowledgeDocument).where(
                and_(*conditions)
            )
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # 查询文档列表
            query = select(KnowledgeDocument).where(and_(*conditions))
            
            # 排序
            if hasattr(KnowledgeDocument, order_by):
                order_column = getattr(KnowledgeDocument, order_by)
                query = query.order_by(
                    order_column.desc() if order_desc else order_column.asc()
                )
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            documents = result.scalars().all()
            
            logger.info(f"查询到 {len(documents)} 个文档，总数: {total}")
            return list(documents), total
            
        except Exception as e:
            logger.error(f"列出文档失败: {str(e)}")
            return [], 0
    
    async def update_document(
        self,
        doc_id: str,
        **updates
    ) -> Optional[KnowledgeDocument]:
        """更新文档"""
        try:
            document = await self.get_document(doc_id)
            if not document:
                return None
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            document.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(document)
            
            # 如果内容更新，重新向量化
            if "content" in updates or "title" in updates:
                await self.vectorize_document(doc_id)
            
            logger.info(f"更新文档成功: {doc_id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新文档失败: {str(e)}")
            raise
    
    async def delete_document(self, doc_id: str, soft_delete: bool = True) -> bool:
        """删除文档"""
        try:
            document = await self.get_document(doc_id)
            if not document:
                return False
            
            if soft_delete:
                # 软删除
                document.status = "deleted"
                await self.db.commit()
            else:
                # 硬删除
                await self.db.delete(document)
                await self.db.commit()
                
                # 从向量库删除
                if document.vector_id:
                    await self.vector_store.delete_document(document.vector_id)
            
            logger.info(f"删除文档: {doc_id} (软删除: {soft_delete})")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    async def vectorize_document(self, doc_id: str) -> bool:
        """
        向量化文档
        
        将文档内容向量化并存储到向量库
        """
        try:
            document = await self.get_document(doc_id)
            if not document:
                return False
            
            # 添加到向量库
            vector_id = await self.vector_store.add_document(
                doc_id=doc_id,
                title=document.title,
                content=document.content,
                doc_type=document.doc_type,
                metadata={
                    "author": document.author,
                    "department": document.department,
                    "tags": document.tags,
                    "keywords": document.keywords,
                    "created_at": document.created_at.isoformat() if document.created_at else None
                }
            )
            
            # 更新向量化状态
            document.is_vectorized = True
            document.vector_id = vector_id
            document.vectorized_at = datetime.utcnow()
            document.embedding_model = self.vector_store.embedding_model_name
            
            await self.db.commit()
            
            logger.info(f"文档向量化成功: {doc_id} -> {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"文档向量化失败: {str(e)}")
            return False
    
    async def batch_vectorize(
        self,
        doc_ids: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        批量向量化
        
        Args:
            doc_ids: 文档ID列表，None表示所有未向量化的文档
            force: 是否强制重新向量化
        """
        try:
            if doc_ids:
                conditions = [KnowledgeDocument.id.in_(doc_ids)]
            else:
                conditions = [KnowledgeDocument.status == "active"]
                if not force:
                    conditions.append(KnowledgeDocument.is_vectorized == False)
            
            result = await self.db.execute(
                select(KnowledgeDocument).where(and_(*conditions))
            )
            documents = result.scalars().all()
            
            success_count = 0
            fail_count = 0
            
            for doc in documents:
                try:
                    success = await self.vectorize_document(doc.id)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"向量化文档 {doc.id} 失败: {str(e)}")
                    fail_count += 1
            
            logger.info(f"批量向量化完成: 成功 {success_count}, 失败 {fail_count}")
            return {
                "total": len(documents),
                "success": success_count,
                "fail": fail_count
            }
            
        except Exception as e:
            logger.error(f"批量向量化失败: {str(e)}")
            raise
    
    async def search_documents(
        self,
        query: str,
        doc_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索文档（结合数据库和向量检索）
        """
        try:
            # 1. 数据库关键词搜索
            conditions = [
                KnowledgeDocument.status == "active",
                or_(
                    KnowledgeDocument.title.contains(query),
                    KnowledgeDocument.content.contains(query)
                )
            ]
            
            if doc_type:
                conditions.append(KnowledgeDocument.doc_type == doc_type)
            
            db_result = await self.db.execute(
                select(KnowledgeDocument)
                .where(and_(*conditions))
                .limit(top_k)
            )
            db_docs = db_result.scalars().all()
            
            # 2. 向量相似度搜索
            vector_results = await self.vector_store.hybrid_search(
                query=query,
                doc_type=doc_type,
                top_k=top_k
            )
            
            # 3. 合并结果
            results = []
            seen_ids = set()
            
            # 优先返回向量检索结果
            for vr in vector_results:
                if vr["id"] not in seen_ids:
                    results.append(vr)
                    seen_ids.add(vr["id"])
            
            # 补充数据库检索结果
            for doc in db_docs:
                if doc.id not in seen_ids:
                    results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "content": doc.content,
                        "doc_type": doc.doc_type,
                        "score": 0.5,  # 数据库检索给予中等分数
                        "metadata": doc.to_dict()
                    })
                    seen_ids.add(doc.id)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []
    
    async def _increment_view_count(self, doc_id: str):
        """增加浏览次数"""
        try:
            await self.db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == doc_id)
                .values(view_count=KnowledgeDocument.view_count + 1)
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"增加浏览次数失败: {str(e)}")
    
    async def increment_reference_count(self, doc_id: str):
        """增加引用次数"""
        try:
            await self.db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == doc_id)
                .values(reference_count=KnowledgeDocument.reference_count + 1)
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"增加引用次数失败: {str(e)}")
    
    # 分类管理
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> KnowledgeCategory:
        """创建分类"""
        try:
            category = KnowledgeCategory(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                parent_id=parent_id
            )
            
            self.db.add(category)
            await self.db.commit()
            await self.db.refresh(category)
            
            logger.info(f"创建分类成功: {category.id}")
            return category
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建分类失败: {str(e)}")
            raise
    
    async def list_categories(self) -> List[KnowledgeCategory]:
        """列出所有分类"""
        try:
            result = await self.db.execute(
                select(KnowledgeCategory).order_by(KnowledgeCategory.sort_order)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"列出分类失败: {str(e)}")
            return []
    
    # 知识库管理
    async def create_knowledge_base(self, name: str, description: str = None) -> KnowledgeBase:
        """创建知识库"""
        knowledge_base = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        self.db.add(knowledge_base)
        await self.db.commit()
        await self.db.refresh(knowledge_base)
        logger.info(f"知识库创建成功: {knowledge_base.name}")
        return knowledge_base
    
    async def add_document_to_knowledge_base(self, document_id: str, knowledge_base_id: str):
        """将文档关联到知识库"""
        # 检查知识库是否存在
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        knowledge_base = kb_result.scalar_one_or_none()
        if not knowledge_base:
            raise ValueError(f"知识库 {knowledge_base_id} 不存在")
        
        # 检查文档是否存在
        doc_result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        if not document:
            raise ValueError(f"文档 {document_id} 不存在")
        
        # 创建关联
        association = KnowledgeBaseDocument(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            document_id=document_id
        )
        self.db.add(association)
        await self.db.commit()
        logger.info(f"文档 {document_id} 已关联到知识库 {knowledge_base_id}")
    
    async def list_documents_in_knowledge_base(self, knowledge_base_id: str):
        """列出知识库中的所有文档"""
        result = await self.db.execute(
            select(Document)
            .join(KnowledgeBaseDocument, KnowledgeBaseDocument.document_id == Document.id)
            .where(KnowledgeBaseDocument.knowledge_base_id == knowledge_base_id)
        )
        return result.scalars().all()
    
    async def list_knowledge_bases_for_document(self, document_id: str):
        """列出文档所属的所有知识库"""
        result = await self.db.execute(
            select(KnowledgeBase)
            .join(KnowledgeBaseDocument, KnowledgeBaseDocument.knowledge_base_id == KnowledgeBase.id)
            .where(KnowledgeBaseDocument.document_id == document_id)
        )
        return result.scalars().all()


async def get_knowledge_service(db: AsyncSession = None) -> KnowledgeService:
    """获取知识库服务实例"""
    if db is None:
        db = await anext(get_db())
    return KnowledgeService(db)
