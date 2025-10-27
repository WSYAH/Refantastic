import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.document import Base

# 测试数据库路径
TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "scripts",
    "data",
    "refantastic.db"
)
os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)

TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


# 使用 pytest_asyncio.fixture 装饰器
@pytest_asyncio.fixture
async def db_session():
    """创建测试数据库会话 - 简化版本"""
    # 创建引擎
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False
    )
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建 session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # 创建并返回 session
    async with async_session_maker() as session:
        yield session
        # 测试结束后回滚
        await session.rollback()
    
    # 清理
    await engine.dispose()


@pytest.fixture
def sample_document_data():
    """测试文档数据"""
    return {
        "title": "测试文档",
        "content": "这是测试文档的内容",
        "doc_type": "general",
        "creator_id": "test-user-123",
        "doc_number": "DOC-2024-001",
        "tags": ["测试", "文档"],
        "metadata": {"key": "value"}
    }


@pytest.fixture
def sample_user_id():
    """测试用户ID"""
    return "test-user-123"


@pytest.fixture
def sample_template_data():
    """示例模板数据"""
    return {
        "name": "请示报告",
        "category": "请示",
        "content": "{{title}}\n\n{{department}}:\n\n{{content}}\n\n特此请示。",
        "variables": ["title", "department", "content"],
        "description": "标准请示报告模板"
    }
