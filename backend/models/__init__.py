"""
模型定义包
导入所有模型类以确保它们被 SQLAlchemy 注册
"""

# 用户和权限相关
from .user import User, Role, Permission, UserRole, RolePermission

# 文档相关
from .document import Document, DocumentVersion

# 知识库相关
from .knowledge import KnowledgeDocument, KnowledgeCategory, KnowledgeBase, KnowledgeBaseDocument

# 模板相关
from .template import Template, TemplateVariable

# 工作流相关
from .workflow import Workflow, WorkflowNode, WorkflowInstance, WorkflowTask

# 审计日志
from .audit import AuditLog

# 导出所有模型，方便其他模块使用
__all__ = [
    # 用户和权限
    "User",
    "Role", 
    "Permission",
    "UserRole",
    "RolePermission",
    # 文档
    "Document",
    "DocumentVersion",
    # 知识库
    "KnowledgeDocument",
    "KnowledgeCategory",
    "KnowledgeBase",
    "KnowledgeBaseDocument",
    # 模板
    "Template",
    "TemplateVariable",
    # 工作流
    "Workflow",
    "WorkflowNode", 
    "WorkflowInstance",
    "WorkflowTask",
    # 审计
    "AuditLog",
]