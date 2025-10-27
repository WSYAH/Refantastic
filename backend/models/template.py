from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from core.database import Base


class Template(Base):
    """公文模板模型"""
    
    __tablename__ = "templates"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    doc_type = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text)
    
    category = Column(String(100))
    tags = Column(JSON, default=list)
    variable_names = Column(JSON, default=list)  # 变量名称列表
    
    is_system = Column(Boolean, default=False)  # 系统模板
    is_active = Column(Boolean, default=True, index=True)
    
    usage_count = Column(Integer, default=0)
    
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"))
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    _metadata = Column(JSON, default=dict)
    
    # 关系
    variables = relationship("TemplateVariable", back_populates="template", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "doc_type": self.doc_type,
            "content": self.content,
            "description": self.description,
            "category": self.category,
            "tags": self.tags or [],
            "variable_names": self.variable_names or [],
            "is_system": self.is_system,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "creator_id": self.creator_id,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self._metadata or {}
        }


class TemplateVariable(Base):
    """模板变量定义模型"""
    
    __tablename__ = "template_variables"
    
    id = Column(String(36), primary_key=True)
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    variable_name = Column(String(100), nullable=False)
    variable_type = Column(String(50), nullable=False)  # text, date, number, select
    label = Column(String(200), nullable=False)
    description = Column(Text)
    
    is_required = Column(Boolean, default=False)
    default_value = Column(Text)
    
    validation_rule = Column(JSON)  # 验证规则
    options = Column(JSON)  # select 类型的选项
    
    sort_order = Column(Integer, default=0)
    
    # 关系
    template = relationship("Template", back_populates="variables")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "variable_name": self.variable_name,
            "variable_type": self.variable_type,
            "label": self.label,
            "description": self.description,
            "is_required": self.is_required,
            "default_value": self.default_value,
            "validation_rule": self.validation_rule,
            "options": self.options,
            "sort_order": self.sort_order
        }
