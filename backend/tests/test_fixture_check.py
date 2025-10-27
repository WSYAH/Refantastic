"""检查 fixture 是否工作"""
import pytest


def test_sample_user_id(sample_user_id):
    """测试普通 fixture"""
    assert sample_user_id == "test-user-123"
    print(f"✅ sample_user_id fixture works: {sample_user_id}")


def test_sample_document_data(sample_document_data):
    """测试文档数据 fixture"""
    assert "title" in sample_document_data
    assert sample_document_data["title"] == "测试文档"
    print(f"✅ sample_document_data fixture works")


@pytest.mark.asyncio
async def test_db_session(db_session):
    """测试数据库 session fixture"""
    assert db_session is not None
    print(f"✅ db_session fixture works: {type(db_session)}")
