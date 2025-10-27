"""
用户权限相关 Schemas
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .common import PaginatedResponse  # 从 common 导入


# ==================== 用户模型 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=50, description="职位")
    phone: Optional[str] = Field(None, max_length=20, description="电话")


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role_ids: Optional[List[str]] = Field(default=[], description="角色ID列表")
    is_active: bool = Field(default=True, description="是否激活")
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=6, max_length=50)
    is_active: Optional[bool] = None
    role_ids: Optional[List[str]] = None
    avatar: Optional[str] = Field(None, max_length=500)


class UserResponse(UserBase):
    """用户响应"""
    id: str
    is_active: bool
    is_superuser: bool
    avatar: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithRoles(UserResponse):
    """带角色的用户响应"""
    roles: List['RoleResponse'] = []


# ==================== 角色模型 ====================

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    code: str = Field(..., min_length=2, max_length=30, description="角色代码")
    description: Optional[str] = Field(None, max_length=500, description="描述")


class RoleCreate(RoleBase):
    """创建角色"""
    permission_ids: Optional[List[str]] = Field(default=[], description="权限ID列表")


class RoleUpdate(BaseModel):
    """更新角色"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    permission_ids: Optional[List[str]] = Field(default=None, description="权限ID列表")


class RoleResponse(RoleBase):
    """角色响应"""
    id: str
    is_system: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleWithPermissions(RoleResponse):
    """带权限的角色响应"""
    permissions: List['PermissionResponse'] = []


# ==================== 权限模型 ====================

class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., min_length=2, max_length=50, description="权限名称")
    code: str = Field(..., description="权限代码，格式: resource:action")
    resource: str = Field(..., min_length=2, max_length=50, description="资源类型")
    action: str = Field(..., description="操作类型")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    @validator('code')
    def validate_code(cls, v, values):
        """验证权限代码格式"""
        if ':' not in v:
            raise ValueError('权限代码必须包含冒号，格式: resource:action')
        return v


class PermissionCreate(PermissionBase):
    """创建权限"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="权限名称")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")


class PermissionResponse(PermissionBase):
    """权限响应"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 认证模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    
    @validator("new_password")
    def validate_new_password(cls, v):
        """验证新密码的复杂性"""
        if not any(c.isupper() for c in v):
            raise ValueError("新密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("新密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("新密码必须包含至少一个数字")
        return v


# ==================== 关联模型 ====================

class UserRoleAssign(BaseModel):
    """用户角色分配"""
    role_ids: List[str] = Field(..., min_length=1, description="角色ID列表")


class RolePermissionAssign(BaseModel):
    """角色权限分配"""
    permission_ids: List[str] = Field(..., min_length=1, description="权限ID列表")


# ==================== 分页响应模型 ====================

class UserListResponse(PaginatedResponse):
    """用户列表响应"""
    items: List[UserWithRoles]


class RoleListResponse(PaginatedResponse):
    """角色列表响应"""
    items: List[RoleWithPermissions]


class PermissionListResponse(PaginatedResponse):
    """权限列表响应"""
    items: List[PermissionResponse]


# 更新前向引用
UserWithRoles.model_rebuild()
RoleWithPermissions.model_rebuild()
