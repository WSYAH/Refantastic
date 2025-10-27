"""
知识库相关 Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class KnowledgeDocumentBase(BaseModel):
    """知识库文档基础模型"""
    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    content: str = Field(..., min_length=1, description="文档内容")
    doc_type: str = Field(..., max_length=100, description="文档类型")
    author: Optional[str] = Field(None, max_length=200, description="作者")
    department: Optional[str] = Field(None, max_length=200, description="部门")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    
    @validator('tags', 'keywords')
    def validate_list_length(cls, v):
        if len(v) > 20:
            raise ValueError('列表长度不能超过 20')
        return v


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """创建知识库文档"""
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    auto_vectorize: bool = Field(True, description="是否自动向量化")


class KnowledgeDocumentUpdate(BaseModel):
    """更新知识库文档"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    doc_type: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    status: Optional[DocumentStatus] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    """知识库文档响应"""
    id: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    is_vectorized: bool
    vector_id: Optional[str] = None
    embedding_model: Optional[str] = None
    quality_score: int
    view_count: int
    reference_count: int
    status: DocumentStatus
    is_public: bool
    created_at: datetime
    updated_at: datetime
    vectorized_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class KnowledgeDocumentList(BaseModel):
    """知识库文档列表响应"""
    documents: List[KnowledgeDocumentResponse]
    total: int
    skip: int
    limit: int


class KnowledgeCategoryBase(BaseModel):
    """知识库分类基础模型"""
    name: str = Field(..., min_length=1, max_length=200, description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    sort_order: int = Field(0, description="排序顺序")


class KnowledgeCategoryCreate(KnowledgeCategoryBase):
    """创建知识库分类"""
    pass


class KnowledgeCategoryResponse(KnowledgeCategoryBase):
    """知识库分类响应"""
    id: str
    doc_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    doc_type: Optional[str] = Field(None, description="文档类型过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    status: DocumentStatus = Field(DocumentStatus.ACTIVE, description="文档状态")
    top_k: int = Field(10, ge=1, le=50, description="返回数量")


class VectorizeRequest(BaseModel):
    """向量化请求"""
    doc_ids: Optional[List[str]] = Field(None, description="文档ID列表")
    force: bool = Field(False, description="是否强制重新向量化")


class VectorizeResponse(BaseModel):
    """向量化响应"""
    total: int
    success: int
    fail: int
    message: str
