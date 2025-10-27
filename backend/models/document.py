from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from core.database import Base


class Document(Base):
    """文档模型"""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    doc_type = Column(String(100), nullable=False, index=True)
    doc_number = Column(String(100), unique=True, index=True)
    
    # 状态：draft, reviewing, approved, published, archived
    status = Column(String(50), default="draft", index=True)
    
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    approver_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="SET NULL"))
    workflow_instance_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="SET NULL"))
    
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    version = Column(Integer, default=1)
    is_public = Column(Boolean, default=False)
    
    published_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    _metadata = Column("metadata", JSON, default=dict)
    
    # 关系 - 仅保留版本关系
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    # 关系 - 添加与知识库的多对多关系
    knowledge_bases = relationship(
        "KnowledgeBaseDocument",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type,
            "doc_number": self.doc_number,
            "status": self.status,
            "creator_id": self.creator_id,
            "approver_id": self.approver_id,
            "template_id": self.template_id,
            "workflow_instance_id": self.workflow_instance_id,
            "tags": self.tags or [],
            "attachments": self.attachments or [],
            "version": self.version,
            "is_public": self.is_public,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self._metadata or {},
            "knowledge_bases": [kb.knowledge_base_id for kb in self.knowledge_bases],  # 所属知识库ID列表
        }


class DocumentVersion(Base):
    """文档版本模型"""
    
    __tablename__ = "document_versions"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    change_type = Column(String(50), nullable=False)  # create, update, restore
    change_description = Column(Text)
    
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    _metadata = Column(JSON, default=dict)
    
    # 关系
    document = relationship("Document", back_populates="versions")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "change_type": self.change_type,
            "change_description": self.change_description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self._metadata or {}
        }
