"""
工作流相关 Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """节点类型枚举"""
    START = "start"
    APPROVAL = "approval"
    CONDITION = "condition"
    END = "end"


class ApproverType(str, Enum):
    """审批人类型枚举"""
    USER = "user"
    ROLE = "role"
    DEPARTMENT = "department"


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class WorkflowBase(BaseModel):
    """工作流基础模型"""
    name: str = Field(..., min_length=1, max_length=200, description="工作流名称")
    doc_type: Optional[str] = Field(None, max_length=100, description="适用文档类型")
    description: Optional[str] = Field(None, description="工作流描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="工作流配置")


class WorkflowCreate(WorkflowBase):
    """创建工作流"""
    is_active: bool = Field(True, description="是否启用")


class WorkflowResponse(WorkflowBase):
    """工作流响应"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowNodeBase(BaseModel):
    """工作流节点基础模型"""
    name: str = Field(..., max_length=200, description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    approver_type: Optional[ApproverType] = Field(None, description="审批人类型")
    approver_id: Optional[str] = Field(None, description="审批人ID")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    sort_order: int = Field(0, description="排序")


class WorkflowNodeCreate(WorkflowNodeBase):
    """创建工作流节点"""
    workflow_id: str = Field(..., description="工作流ID")


class WorkflowNodeResponse(WorkflowNodeBase):
    """工作流节点响应"""
    id: str
    workflow_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowWithNodes(WorkflowResponse):
    """带节点的工作流响应"""
    nodes: List[WorkflowNodeResponse]


class WorkflowInstanceResponse(BaseModel):
    """工作流实例响应"""
    id: str
    workflow_id: str
    document_id: str
    status: WorkflowStatus
    current_node_id: Optional[str] = None
    initiator_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class WorkflowTaskResponse(BaseModel):
    """工作流任务响应"""
    id: str
    instance_id: str
    node_id: str
    assignee_id: str
    status: TaskStatus
    comment: Optional[str] = None
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class WorkflowStartRequest(BaseModel):
    """启动工作流请求"""
    workflow_id: str = Field(..., description="工作流ID")
    document_id: str = Field(..., description="文档ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class WorkflowApproveRequest(BaseModel):
    """审批工作流请求"""
    task_id: str = Field(..., description="任务ID")
    action: TaskStatus = Field(..., description="审批动作")
    comment: Optional[str] = Field(None, max_length=1000, description="审批意见")


class WorkflowHistoryResponse(BaseModel):
    """工作流历史响应"""
    instance: WorkflowInstanceResponse
    tasks: List[WorkflowTaskResponse]
    workflow: WorkflowResponse
