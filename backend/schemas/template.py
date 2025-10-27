"""
模板管理相关 Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class VariableType(str, Enum):
    """变量类型枚举"""
    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    SELECT = "select"
    TEXTAREA = "textarea"


class TemplateBase(BaseModel):
    """模板基础模型"""
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    doc_type: str = Field(..., max_length=100, description="文档类型")
    content: str = Field(..., min_length=1, description="模板内容")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")


class TemplateCreate(TemplateBase):
    """创建模板"""
    is_system: bool = Field(False, description="是否系统模板")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class TemplateUpdate(BaseModel):
    """更新模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class TemplateResponse(TemplateBase):
    """模板响应"""
    id: str
    is_system: bool
    is_active: bool
    usage_count: int
    creator_id: str
    version: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class TemplateVariableBase(BaseModel):
    """模板变量基础模型"""
    variable_name: str = Field(..., max_length=100, description="变量名")
    variable_type: VariableType = Field(..., description="变量类型")
    label: str = Field(..., max_length=200, description="显示标签")
    description: Optional[str] = Field(None, description="变量描述")
    is_required: bool = Field(False, description="是否必填")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    options: Optional[List[str]] = Field(None, description="选项列表（用于 select 类型）")
    sort_order: int = Field(0, description="排序")
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('variable_type') == VariableType.SELECT and not v:
            raise ValueError('select 类型变量必须提供选项列表')
        return v


class TemplateVariableCreate(TemplateVariableBase):
    """创建模板变量"""
    template_id: str = Field(..., description="模板ID")


class TemplateVariableResponse(TemplateVariableBase):
    """模板变量响应"""
    id: str
    template_id: str
    
    class Config:
        from_attributes = True


class TemplateWithVariables(TemplateResponse):
    """带变量的模板响应"""
    variables: List[TemplateVariableResponse]


class TemplateRenderRequest(BaseModel):
    """模板渲染请求"""
    template_id: str = Field(..., description="模板ID")
    variables: Dict[str, Any] = Field(..., description="变量值")


class TemplateRenderResponse(BaseModel):
    """模板渲染响应"""
    content: str = Field(..., description="渲染后的内容")
    template_id: str
    variables_used: Dict[str, Any]
