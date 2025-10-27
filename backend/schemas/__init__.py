"""Schemas 包"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    StatusResponse,
    TimestampMixin
)

from .user import (
    # 用户
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithRoles,
    UserListResponse,
    # 角色
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissions,
    RoleListResponse,
    # 权限
    PermissionBase,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionListResponse,
    # 认证
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
    # 关联
    UserRoleAssign,
    RolePermissionAssign,
)


__all__ = [
    # 通用
    "PaginationParams",
    "PaginatedResponse",
    "StatusResponse",
    "TimestampMixin",
    # 用户
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserWithRoles",
    "UserListResponse",
    # 角色
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "RoleListResponse",
    # 权限
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "PermissionListResponse",
    # 认证
    "LoginRequest",
    "TokenResponse",
    "ChangePasswordRequest",
    # 关联
    "UserRoleAssign",
    "RolePermissionAssign",
]
