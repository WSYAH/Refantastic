"""角色管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import uuid
import math

from core.database import get_db
from core.security import get_current_user, get_current_active_superuser
from models import User, Role, Permission, RolePermission
from schemas.user import (
    RoleCreate, RoleUpdate, RoleResponse, RoleWithPermissions,
    RoleListResponse, PermissionResponse, RolePermissionAssign
)


router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("", response_model=RoleListResponse, summary="获取角色列表")
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_system: Optional[bool] = Query(None, description="是否系统角色"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分页查询角色列表"""
    # 构建查询
    query = select(Role)
    
    # 搜索条件
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Role.name.like(search_pattern),
                Role.code.like(search_pattern)
            )
        )
    
    # 系统角色筛选
    if is_system is not None:
        query = query.where(Role.is_system == is_system)
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # 为每个角色查询权限
    roles_with_permissions = []
    for role in roles:
        perms_result = await db.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        permissions = perms_result.scalars().all()
        
        role_dict = role.to_dict()
        role_dict['permissions'] = [
            PermissionResponse.model_validate(perm) for perm in permissions
        ]
        roles_with_permissions.append(RoleWithPermissions(**role_dict))
    
    return RoleListResponse(
        items=roles_with_permissions,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size)
    )


@router.get("/{role_id}", response_model=RoleWithPermissions, summary="获取角色详情")
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详细信息（包含权限列表）"""
    # 查询角色
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 查询权限
    perms_result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    permissions = perms_result.scalars().all()
    
    role_dict = role.to_dict()
    role_dict['permissions'] = [
        PermissionResponse.model_validate(perm) for perm in permissions
    ]
    
    return RoleWithPermissions(**role_dict)


@router.post("", response_model=RoleResponse, summary="创建角色")
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """创建新角色"""
    # 检查角色代码是否存在
    result = await db.execute(select(Role).where(Role.code == role_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色代码已存在"
        )
    
    # 创建角色
    new_role = Role(
        id=str(uuid.uuid4()),
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
        is_system=False
    )
    
    db.add(new_role)
    await db.flush()
    
    # 分配权限
    if role_data.permission_ids:
        for perm_id in role_data.permission_ids:
            role_perm = RolePermission(
                id=str(uuid.uuid4()),
                role_id=new_role.id,
                permission_id=perm_id
            )
            db.add(role_perm)
    
    await db.commit()
    await db.refresh(new_role)
    
    return RoleResponse.model_validate(new_role)


@router.put("/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新角色信息"""
    # 查询角色
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 系统角色不能修改名称和代码
    if role.is_system and ('name' in role_data.model_dump(exclude_unset=True) or 
                          'code' in role_data.model_dump(exclude_unset=True)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统角色不能修改名称和代码"
        )
    
    # 更新字段
    update_data = role_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field != 'permission_ids':
            setattr(role, field, value)
    
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", summary="删除角色")
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """删除角色（系统角色不可删除）"""
    # 查询角色
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 系统角色不能删除
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统角色不能删除"
        )
    
    await db.delete(role)
    await db.commit()
    
    return {"message": "角色删除成功"}


# ==================== 角色权限关联 ====================

@router.get("/{role_id}/permissions", response_model=list[PermissionResponse], summary="获取角色权限")
async def get_role_permissions(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色的所有权限"""
    # 查询权限
    perms_result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    permissions = perms_result.scalars().all()
    
    return [PermissionResponse.model_validate(perm) for perm in permissions]


@router.post("/{role_id}/permissions", summary="为角色分配权限")
async def assign_role_permissions(
    role_id: str,
    perm_data: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """为角色添加权限"""
    # 查询角色
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 添加权限
    for perm_id in perm_data.permission_ids:
        # 检查权限是否存在
        perm_result = await db.execute(
            select(Permission).where(Permission.id == perm_id)
        )
        if not perm_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"权限 {perm_id} 不存在"
            )
        
        # 检查是否已存在
        existing = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == perm_id
            )
        )
        if not existing.scalar_one_or_none():
            role_perm = RolePermission(
                id=str(uuid.uuid4()),
                role_id=role_id,
                permission_id=perm_id
            )
            db.add(role_perm)
    
    await db.commit()
    
    return {"message": "权限分配成功"}


@router.delete("/{role_id}/permissions/{permission_id}", summary="移除角色权限")
async def remove_role_permission(
    role_id: str,
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """移除角色的指定权限"""
    # 查询关联
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
    )
    role_perm = result.scalar_one_or_none()
    
    if not role_perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色权限关联不存在"
        )
    
    await db.delete(role_perm)
    await db.commit()
    
    return {"message": "权限移除成功"}
