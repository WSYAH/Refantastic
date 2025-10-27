"""
文档管理相关 Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str = Field(..., description="文档标题", max_length=500)
    content: str = Field(..., description="文档内容")
    doc_type: str = Field(..., description="文档类型", max_length=100)
    doc_number: Optional[str] = Field(None, description="文号", max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="附件列表")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class DocumentCreate(DocumentBase):
    """创建文档请求"""
    creator_id: str = Field(..., description="创建人ID")
    template_id: Optional[str] = Field(None, description="使用的模板ID")


class DocumentUpdate(BaseModel):
    """更新文档请求"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """文档响应"""
    id: str
    status: str
    creator_id: str
    approver_id: Optional[str] = None
    template_id: Optional[str] = None
    workflow_instance_id: Optional[str] = None
    version: int
    is_public: bool
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentVersionResponse(BaseModel):
    """文档版本响应"""
    id: str
    document_id: str
    version: int
    title: str
    content: str
    change_type: str
    change_description: Optional[str] = None
    created_by: str
    created_at: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True
