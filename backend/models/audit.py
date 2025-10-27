from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey
from datetime import datetime
from typing import Dict, Any

from core.database import Base


class AuditLog(Base):
    """审计日志模型"""
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    action = Column(String(100), nullable=False, index=True)  # 操作类型
    resource_type = Column(String(100), nullable=False, index=True)  # 资源类型
    resource_id = Column(String(36), index=True)  # 资源ID
    
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    request_data = Column(JSON)  # 请求数据
    response_status = Column(Integer)  # 响应状态码
    error_message = Column(Text)  # 错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_data": self.request_data,
            "response_status": self.response_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
