"""用户管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import uuid
import bcrypt
import math

from core.database import get_db
from core.security import get_current_user, get_current_active_superuser
from models import User, Role, UserRole
from schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserWithRoles,
    UserListResponse, RoleResponse, UserRoleAssign
)


router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    department: Optional[str] = Query(None, description="部门筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分页查询用户列表
    
    支持按关键词、部门、状态筛选
    """
    # 构建查询
    query = select(User)
    
    # 搜索条件
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern),
                User.full_name.like(search_pattern)
            )
        )
    
    # 部门筛选
    if department:
        query = query.where(User.department == department)
    
    # 状态筛选
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # 查询总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 为每个用户查询角色
    users_with_roles = []
    for user in users:
        roles_result = await db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        )
        roles = roles_result.scalars().all()
        
        user_dict = user.to_dict()
        user_dict['roles'] = [RoleResponse.model_validate(role) for role in roles]
        users_with_roles.append(UserWithRoles(**user_dict))
    
    return UserListResponse(
        items=users_with_roles,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size)
    )


@router.get("/{user_id}", response_model=UserWithRoles, summary="获取用户详情")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的详细信息"""
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询角色
    roles_result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    roles = roles_result.scalars().all()
    
    user_dict = user.to_dict()
    user_dict['roles'] = [RoleResponse.model_validate(role) for role in roles]
    
    return UserWithRoles(**user_dict)


@router.post("", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    创建新用户
    
    需要超级管理员权限
    """
    # 检查用户名是否存在
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否存在
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 哈希密码
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # 创建用户
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed.decode('utf-8'),
        full_name=user_data.full_name,
        department=user_data.department,
        position=user_data.position,
        phone=user_data.phone,
        is_active=user_data.is_active,
        is_superuser=False
    )
    
    db.add(new_user)
    await db.flush()
    
    # 分配角色
    if user_data.role_ids:
        for role_id in user_data.role_ids:
            user_role = UserRole(
                id=str(uuid.uuid4()),
                user_id=new_user.id,
                role_id=role_id
            )
            db.add(user_role)
    
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新用户信息
    
    超级管理员可以更新任何用户，普通用户只能更新自己的部分信息
    """
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)
    
    # 普通用户不能修改某些字段
    if not current_user.is_superuser:
        update_data.pop('is_active', None)
        update_data.pop('role_ids', None)
    
    # 检查邮箱唯一性
    if 'email' in update_data and update_data['email'] != user.email:
        result = await db.execute(
            select(User).where(User.email == update_data['email'])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
    
    # 更新密码
    if 'password' in update_data:
        password_bytes = update_data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        user.password_hash = hashed.decode('utf-8')
        update_data.pop('password')
    
    # 更新角色
    if 'role_ids' in update_data and current_user.is_superuser:
        # 删除旧角色
        await db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        await db.execute(
            UserRole.__table__.delete().where(UserRole.user_id == user_id)
        )
        
        # 添加新角色
        for role_id in update_data['role_ids']:
            user_role = UserRole(
                id=str(uuid.uuid4()),
                user_id=user_id,
                role_id=role_id
            )
            db.add(user_role)
        
        update_data.pop('role_ids')
    
    # 更新用户信息
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    删除用户
    
    需要超级管理员权限
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户（会级联删除用户角色关联）
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户删除成功"}


# ==================== 用户角色关联 ====================

@router.get("/{user_id}/roles", response_model=list[RoleResponse], summary="获取用户角色")
async def get_user_roles(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的所有角色"""
    # 查询用户是否存在
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 查询角色
    roles_result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    roles = roles_result.scalars().all()
    
    return [RoleResponse.model_validate(role) for role in roles]


@router.post("/{user_id}/roles", summary="为用户分配角色")
async def assign_user_roles(
    user_id: str,
    role_data: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """为用户添加角色"""
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 添加角色
    for role_id in role_data.role_ids:
        # 检查角色是否存在
        role_result = await db.execute(select(Role).where(Role.id == role_id))
        if not role_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色 {role_id} 不存在"
            )
        
        # 检查是否已存在
        existing = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        )
        if not existing.scalar_one_or_none():
            user_role = UserRole(
                id=str(uuid.uuid4()),
                user_id=user_id,
                role_id=role_id
            )
            db.add(user_role)
    
    await db.commit()
    
    return {"message": "角色分配成功"}


@router.delete("/{user_id}/roles/{role_id}", summary="移除用户角色")
async def remove_user_role(
    user_id: str,
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """移除用户的指定角色"""
    # 查询关联
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
    )
    user_role = result.scalar_one_or_none()
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户角色关联不存在"
        )
    
    await db.delete(user_role)
    await db.commit()
    
    return {"message": "角色移除成功"}
