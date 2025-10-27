from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from core.database import Base


class KnowledgeDocument(Base):
    """知识库文档模型"""
    
    __tablename__ = "knowledge_documents"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    doc_type = Column(String(100), nullable=False, index=True)
    
    # 元数据
    author = Column(String(200))
    department = Column(String(200))
    tags = Column(JSON, default=list)  # 标签列表
    keywords = Column(JSON, default=list)  # 关键词列表
    
    # 文件信息
    file_path = Column(String(1000))  # 原始文件路径
    file_type = Column(String(50))  # pdf, docx, txt 等
    file_size = Column(Integer)  # 字节
    
    # 向量化状态
    is_vectorized = Column(Boolean, default=False, index=True)
    vector_id = Column(String(100))  # 向量库中的ID
    embedding_model = Column(String(200))  # 使用的嵌入模型
    
    # 质量评分
    quality_score = Column(Integer, default=0)  # 0-100
    view_count = Column(Integer, default=0)
    reference_count = Column(Integer, default=0)
    
    # 状态
    status = Column(String(50), default="active")  # active, archived, deleted
    is_public = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vectorized_at = Column(DateTime)
    
    # 额外元数据
    _metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type,
            "author": self.author,
            "department": self.department,
            "tags": self.tags or [],
            "keywords": self.keywords or [],
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "is_vectorized": self.is_vectorized,
            "vector_id": self.vector_id,
            "quality_score": self.quality_score,
            "view_count": self.view_count,
            "reference_count": self.reference_count,
            "status": self.status,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "vectorized_at": self.vectorized_at.isoformat() if self.vectorized_at else None,
            "metadata": self._metadata or {}
        }


class KnowledgeCategory(Base):
    """知识库分类模型"""
    
    __tablename__ = "knowledge_categories"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(String(36))  # 父分类ID，支持层级
    
    icon = Column(String(100))
    sort_order = Column(Integer, default=0)
    
    doc_count = Column(Integer, default=0)  # 文档数量
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "doc_count": self.doc_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # 知识库唯一名称
    description = Column(String(500), nullable=True)  # 知识库描述
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    documents = relationship(
        "KnowledgeBaseDocument",
        back_populates="knowledge_base",
        cascade="all, delete-orphan"
    )


class KnowledgeBaseDocument(Base):
    """知识库与文档的关联模型"""
    __tablename__ = "knowledge_base_documents"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "document_id", name="uq_knowledge_base_document"),
    )
    
    id = Column(String(36), primary_key=True)
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    document = relationship("Document", back_populates="knowledge_bases")
