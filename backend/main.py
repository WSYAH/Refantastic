from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
    get_redoc_html,
)
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger

from config import get_settings
from api import router as api_router
from core.vector_store import get_vector_store
from core.database import init_db
from scripts.init_default_data import ensure_default_data


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动 Refantastic 公文生成系统...")
    
    # 初始化数据库
    await init_db()
    
    # 初始化向量存储
    vector_store = get_vector_store()
    await vector_store.initialize()
    
    logger.info("系统启动完成")
    yield
    
    # 清理资源
    logger.info("关闭系统...")
    await vector_store.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Refantastic 公文生成系统 API
    
    ### 功能模块
    
    * **用户管理** - 用户、角色、权限管理
    * **文档管理** - 文档创建、编辑、审批、发布
    * **模板管理** - 文档模板的增删改查
    * **工作流** - 审批流程管理
    * **知识库** - 知识文档和向量检索
    * **AI 生成** - 基于 LLM 的文档生成
    
    ### 认证方式
    
    使用 JWT Token 进行身份认证，请在请求头中添加：
    ```
    Authorization: Bearer <your_token>
    ```
    
    ### 测试账号
    
    - 管理员: admin / password123
    - 经理: manager1 / password123
    - 员工: employee1 / password123
    """,
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI 路径
    redoc_url="/redoc",  # ReDoc 路径
    openapi_url="/openapi.json",  # OpenAPI schema 路径
    contact={
        "name": "Refantastic Team",
        "email": "support@refantastic.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # 默认不展开模型
        "docExpansion": "list",  # 默认展开方式: "list", "full", "none"
        "filter": True,  # 启用搜索过滤
        "showRequestHeaders": True,  # 显示请求头
        "syntaxHighlight.theme": "monokai",  # 代码高亮主题
    }
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1", tags=["API v1"])


@app.get("/", tags=["Health"])
async def root():
    """
    根路径 - 系统状态
    
    返回系统基本信息和可用的文档链接
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": {
            "swagger": "http://localhost:8000/docs",
            "redoc": "http://localhost:8000/redoc",
            "openapi": "http://localhost:8000/openapi.json"
        },
        "api": {
            "base": "/api/v1",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康检查接口
    
    用于监控系统运行状态，包括数据库连接和向量存储状态
    """
    return {
        "status": "healthy",
        "database": "connected",
        "vector_store": "initialized",
        "version": settings.APP_VERSION
    }


# 可选：自定义文档页面（如果需要更多定制）
@app.get("/docs-custom", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义 Swagger UI"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - 自定义文档",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc-custom", include_in_schema=False)
async def custom_redoc_html():
    """自定义 ReDoc"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - 自定义文档",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("启动 Refantastic API 服务")
    logger.info("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    # 确保默认数据存在
    await ensure_default_data()
    
    logger.info("=" * 60)
    logger.info("✅ 应用启动完成")
    logger.info(f"📝 API 文档: http://localhost:8000/docs")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    
    # 打印启动信息
    logger.info("\n" + "=" * 70)
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 70)
    logger.info(f"📍 服务地址:        http://localhost:8000")
    logger.info(f"📚 Swagger UI:     http://localhost:8000/docs")
    logger.info(f"📖 ReDoc:          http://localhost:8000/redoc")
    logger.info(f"🔍 健康检查:        http://localhost:8000/health")
    logger.info(f"📄 OpenAPI Schema: http://localhost:8000/openapi.json")
    logger.info(f"🐛 调试模式:        {settings.DEBUG}")
    logger.info(f"🗄️  数据库:         {settings.DATABASE_URL}")
    logger.info("=" * 70)
    logger.info("💡 提示：")
    logger.info("   - Swagger UI 提供交互式 API 测试")
    logger.info("   - ReDoc 提供美观的文档浏览")
    logger.info("   - 按 Ctrl+C 停止服务")
    logger.info("=" * 70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
