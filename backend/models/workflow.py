from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from core.database import Base


class Workflow(Base):
    """工作流定义模型"""
    
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    doc_type = Column(String(100), index=True)  # 适用的文档类型
    description = Column(Text)
    
    is_active = Column(Boolean, default=True, index=True)
    
    config = Column(JSON, nullable=False, default=dict)  # 工作流配置
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    instances = relationship("WorkflowInstance", back_populates="workflow")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "doc_type": self.doc_type,
            "description": self.description,
            "is_active": self.is_active,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class WorkflowNode(Base):
    """工作流节点模型"""
    
    __tablename__ = "workflow_nodes"
    
    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    node_type = Column(String(50), nullable=False)  # start, approval, condition, end
    
    # 审批人设置
    approver_type = Column(String(50))  # user, role, department
    approver_id = Column(String(36))
    
    config = Column(JSON, default=dict)  # 节点配置
    sort_order = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    workflow = relationship("Workflow", back_populates="nodes")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "node_type": self.node_type,
            "approver_type": self.approver_type,
            "approver_id": self.approver_id,
            "config": self.config or {},
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WorkflowInstance(Base):
    """工作流实例模型"""
    
    __tablename__ = "workflow_instances"
    
    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 状态：pending, running, completed, rejected, cancelled
    status = Column(String(50), nullable=False, index=True)
    
    current_node_id = Column(String(36), ForeignKey("workflow_nodes.id", ondelete="SET NULL"))
    initiator_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    _metadata = Column(JSON, default=dict)
    
    # 关系
    workflow = relationship("Workflow", back_populates="instances")
    tasks = relationship("WorkflowTask", back_populates="instance", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "document_id": self.document_id,
            "status": self.status,
            "current_node_id": self.current_node_id,
            "initiator_id": self.initiator_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self._metadata or {}
        }



class WorkflowTask(Base):
    """工作流任务模型"""
    
    __tablename__ = "workflow_tasks"
    
    id = Column(String(36), primary_key=True)
    instance_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(36), ForeignKey("workflow_nodes.id", ondelete="RESTRICT"), nullable=False)
    
    assignee_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # 状态：pending, approved, rejected, cancelled
    status = Column(String(50), nullable=False, index=True)
    comment = Column(Text)  # 审批意见
    
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    _metadata = Column(JSON, default=dict)
    
    # 关系
    instance = relationship("WorkflowInstance", back_populates="tasks")
    node = relationship("WorkflowNode")
    assignee = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "node_id": self.node_id,
            "assignee_id": self.assignee_id,
            "status": self.status,
            "comment": self.comment,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self._metadata or {}
    }