"""
如果上面的配置仍有问题，使用这个简化版本替换 conftest.py
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.document import Base

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "scripts", "data", "refantastic.db"
)
os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)

TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest_asyncio.fixture
async def db_session():
    """简化版 db_session fixture"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建 session
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def sample_document_data():
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
    return "test-user-123"
