"""
通用 Schemas
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from datetime import datetime


T = TypeVar('T')


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页记录数")
    order_by: Optional[str] = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


class PaginatedResponse(BaseModel):
    """分页响应基类"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")
    
    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    """状态响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class TimestampMixin(BaseModel):
    """时间戳 Mixin"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
