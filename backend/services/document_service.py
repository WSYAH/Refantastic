from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from datetime import datetime
import uuid
from loguru import logger

from models.document import Document, DocumentVersion


class DocumentService:
    """文档服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_document(
        self,
        title: str,
        content: str,
        doc_type: str,
        creator_id: str,
        doc_number: Optional[str] = None,
        template_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """创建文档"""
        try:
            doc_id = str(uuid.uuid4())
            
            document = Document(
                id=doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                doc_number=doc_number,
                creator_id=creator_id,
                template_id=template_id,
                tags=tags or [],
                attachments=attachments or [],
                metadata=metadata or {},
                status="draft",
                version=1,
                created_at=datetime.utcnow()
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # 创建第一个版本
            await self._create_version(
                document_id=doc_id,
                version=1,
                title=title,
                content=content,
                change_type="create",
                created_by=creator_id
            )
            
            logger.info(f"创建文档成功: {doc_id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建文档失败: {str(e)}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        try:
            result = await self.db.execute(
                select(Document).where(Document.id == doc_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取文档失败: {str(e)}")
            return None
    
    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        creator_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[List[Document], int]:
        """
        获取文档列表（支持筛选和分页）
        
        所有筛选参数为 None 时，返回所有文档
        """
        logger.info(f"查询文档列表 - 参数: doc_type={doc_type}, status={status}, creator_id={creator_id}, is_public={is_public}")
        
        # 构建查询
        query = select(Document)
        
        # 只在参数不为 None 时添加过滤条件
        if doc_type is not None:
            query = query.where(Document.doc_type == doc_type)
            logger.info(f"添加 doc_type 过滤: {doc_type}")
        
        if status is not None:
            query = query.where(Document.status == status)
            logger.info(f"添加 status 过滤: {status}")
        
        if creator_id is not None:
            query = query.where(Document.creator_id == creator_id)
            logger.info(f"添加 creator_id 过滤: {creator_id}")
        
        if is_public is not None:
            query = query.where(Document.is_public == is_public)
            logger.info(f"添加 is_public 过滤: {is_public}")
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        logger.info(f"查询到文档总数: {total}")
        
        # 排序
        order_column = getattr(Document, order_by, Document.created_at)
        if order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        # 分页
        query = query.offset(skip).limit(limit)
        
        # 执行查询
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        logger.info(f"返回文档数量: {len(documents)}")
        
        return documents, total
    
    async def update_document(self, doc_id: str, **updates) -> Optional[Document]:
        """更新文档"""
        try:
            document = await self.get_document(doc_id)
            if not document:
                return None
            
            old_content = document.content
            old_title = document.title
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            document.updated_at = datetime.utcnow()
            
            # 内容变更，增加版本号
            if "content" in updates or "title" in updates:
                document.version += 1
                await self._create_version(
                    document_id=doc_id,
                    version=document.version,
                    title=document.title,
                    content=document.content,
                    change_type="update",
                    created_by=document.creator_id,
                    change_description="内容更新"
                )
            
            await self.db.commit()
            await self.db.refresh(document)
            
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
                document.status = "archived"
                await self.db.commit()
            else:
                await self.db.delete(document)
                await self.db.commit()
            
            logger.info(f"删除文档: {doc_id} (软删除: {soft_delete})")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除文档失败: {str(e)}")
            return False
    
    async def publish_document(self, doc_id: str) -> Optional[Document]:
        """发布文档"""
        return await self.update_document(
            doc_id,
            status="published",
            published_at=datetime.utcnow()
        )
    
    async def archive_document(self, doc_id: str) -> Optional[Document]:
        """归档文档"""
        return await self.update_document(doc_id, status="archived")
    
    async def get_document_versions(self, doc_id: str) -> List[DocumentVersion]:
        """获取文档版本历史"""
        try:
            result = await self.db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == doc_id)
                .order_by(DocumentVersion.version.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取文档版本失败: {str(e)}")
            return []
    
    async def restore_version(self, doc_id: str, version_id: str) -> Optional[Document]:
        """恢复文档到指定版本"""
        try:
            version_result = await self.db.execute(
                select(DocumentVersion).where(DocumentVersion.id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version or version.document_id != doc_id:
                return None
            
            document = await self.update_document(
                doc_id,
                title=version.title,
                content=version.content
            )
            
            if document:
                await self._create_version(
                    document_id=doc_id,
                    version=document.version,
                    title=version.title,
                    content=version.content,
                    change_type="restore",
                    created_by=document.creator_id,
                    change_description=f"恢复到版本 {version.version}"
                )
            
            return document
            
        except Exception as e:
            logger.error(f"恢复文档版本失败: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取文档统计"""
        try:
            # 总数
            total_result = await self.db.execute(select(func.count()).select_from(Document))
            total = total_result.scalar()
            
            # 按状态统计
            status_result = await self.db.execute(
                select(Document.status, func.count())
                .group_by(Document.status)
            )
            status_stats = {row[0]: row[1] for row in status_result}
            
            # 按类型统计
            type_result = await self.db.execute(
                select(Document.doc_type, func.count())
                .group_by(Document.doc_type)
            )
            type_stats = {row[0]: row[1] for row in type_result}
            
            return {
                "total": total,
                "by_status": status_stats,
                "by_type": type_stats
            }
            
        except Exception as e:
            logger.error(f"获取文档统计失败: {str(e)}")
            return {}
    
    async def _create_version(
        self,
        document_id: str,
        version: int,
        title: str,
        content: str,
        change_type: str,
        created_by: str,
        change_description: Optional[str] = None
    ):
        """创建文档版本"""
        try:
            version_obj = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=document_id,
                version=version,
                title=title,
                content=content,
                change_type=change_type,
                change_description=change_description,
                created_by=created_by,
                created_at=datetime.utcnow()
            )
            
            self.db.add(version_obj)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"创建文档版本失败: {str(e)}")
            raise
