from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from loguru import logger

from config import get_settings


settings = get_settings()

# 根据数据库类型配置引擎参数
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# SQLite 特殊配置
if settings.DATABASE_TYPE == "sqlite":
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,  # SQLite 使用静态连接池
    })
else:
    # PostgreSQL 配置
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基类
Base = declarative_base()


async def init_db():
    """初始化数据库"""
    logger.info(f"初始化数据库 ({settings.DATABASE_TYPE})...")
    logger.info(f"数据库路径: {settings.DATABASE_URL}")
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ 数据库表创建完成")


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
