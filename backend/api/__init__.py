from fastapi import APIRouter

from api.documents import router as documents_router
from api.knowledge import router as knowledge_router
from api.generation import router as generation_router
from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.roles import router as roles_router

router = APIRouter()

router.include_router(documents_router, prefix="/documents", tags=["文档管理"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])
router.include_router(generation_router, prefix="/generation", tags=["公文生成"])
router.include_router(auth_router, prefix="/auth", tags=["认证管理"])
router.include_router(users_router, prefix="/users", tags=["用户管理"])
router.include_router(roles_router, prefix="/roles", tags=["角色管理"])