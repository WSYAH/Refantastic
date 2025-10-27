"""认证相关 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import bcrypt

from core.database import get_db
from models import User, Role, UserRole
from schemas.user import (
    LoginRequest, TokenResponse, ChangePasswordRequest,
    UserResponse, UserWithRoles, RoleResponse
)
from core.security import create_access_token, get_current_user


router = APIRouter(prefix="/auth", tags=["认证管理"])


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回访问令牌和用户信息
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 验证密码
    password_bytes = login_data.password.encode('utf-8')
    if not bcrypt.checkpw(password_bytes, user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # 生成访问令牌
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出
    
    客户端应删除本地存储的令牌
    """
    return {"message": "登出成功"}


@router.get("/me", response_model=UserWithRoles, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户的详细信息，包括角色列表
    """
    # 查询用户角色
    roles_result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    roles = roles_result.scalars().all()
    
    # 构造响应
    user_dict = current_user.to_dict()
    user_dict['roles'] = [RoleResponse.model_validate(role) for role in roles]
    
    return UserWithRoles(**user_dict)


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    - **old_password**: 旧密码
    - **new_password**: 新密码
    """
    # 验证旧密码
    old_password_bytes = password_data.old_password.encode('utf-8')
    if not bcrypt.checkpw(old_password_bytes, current_user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 哈希新密码
    new_password_bytes = password_data.new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(new_password_bytes, salt)
    
    # 更新密码
    current_user.password_hash = hashed.decode('utf-8')
    await db.commit()
    
    return {"message": "密码修改成功"}
