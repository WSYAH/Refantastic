import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.document_service import DocumentService
from models.document import Document


class TestDocumentService:
    """文档服务测试类"""
    
    @pytest.mark.asyncio
    async def test_create_document(self, db_session, sample_document_data, sample_user_id):
        """测试创建文档"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        assert document is not None
        assert document.id is not None
        assert document.title == sample_document_data["title"]
        assert document.content == sample_document_data["content"]
        assert document.doc_type == sample_document_data["doc_type"]
        assert document.creator_id == sample_user_id
        assert document.status == "draft"
        assert document.version == 1
        
        # 验证版本历史
        versions = await service.get_document_versions(document.id)
        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].change_type == "create"
    
    @pytest.mark.asyncio
    async def test_get_document(self, db_session, sample_document_data):
        """测试获取文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        created_doc = await service.create_document(**sample_document_data)
        
        # 获取文档
        document = await service.get_document(created_doc.id)
        
        assert document is not None
        assert document.id == created_doc.id
        assert document.title == created_doc.title
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, db_session):
        """测试获取不存在的文档"""
        service = DocumentService(db_session)
        
        document = await service.get_document("non-existent-id")
        
        assert document is None
    
    @pytest.mark.asyncio
    async def test_list_documents(self, db_session, sample_document_data, sample_user_id):
        """测试列出文档"""
        service = DocumentService(db_session)
        
        # 创建多个文档
        await service.create_document(**sample_document_data)
        await service.create_document(
            title="测试文档2",
            content="内容2",
            doc_type="general",
            creator_id=sample_user_id
        )
        
        # 列出文档
        documents, total = await service.list_documents(status="draft")
        
        assert total >= 2
        assert len(documents) >= 2
    
    @pytest.mark.asyncio
    async def test_list_documents_with_filters(self, db_session, sample_document_data, sample_user_id):
        """测试带过滤条件列出文档"""
        service = DocumentService(db_session)
        
        # 创建不同类型的文档
        await service.create_document(**sample_document_data)
        await service.create_document(
            title="报告文档",
            content="报告内容",
            doc_type="report",
            creator_id=sample_user_id
        )
        
        # 按类型过滤
        documents, total = await service.list_documents(
            doc_type="general",
            status="draft"
        )
        
        assert all(doc.doc_type == "general" for doc in documents)
        
        # 按创建者过滤
        documents, total = await service.list_documents(
            creator_id=sample_user_id,
            status="draft"
        )
        
        assert all(doc.creator_id == sample_user_id for doc in documents)
    
    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, db_session, sample_document_data, sample_user_id):
        """测试文档列表分页"""
        service = DocumentService(db_session)
        
        # 创建多个文档
        for i in range(5):
            await service.create_document(
                title=f"文档{i}",
                content=f"内容{i}",
                doc_type="general",
                creator_id=sample_user_id
            )
        
        # 测试分页
        documents, total = await service.list_documents(
            status="draft",
            skip=0,
            limit=2
        )
        
        assert len(documents) <= 2
        assert total >= 5
    
    @pytest.mark.asyncio
    async def test_update_document(self, db_session, sample_document_data):
        """测试更新文档"""
        service = DocumentService(db_session)
        
        # 创建文档
        document = await service.create_document(**sample_document_data)
        
        # 更新文档
        updated_title = "更新后的标题"
        updated_doc = await service.update_document(
            document.id,
            title=updated_title
        )
        
        assert updated_doc is not None
        assert updated_doc.title == updated_title
        assert updated_doc.version == 2
        
        # 验证版本历史
        versions = await service.get_document_versions(document.id)
        assert len(versions) == 2
    
    @pytest.mark.asyncio
    async def test_update_document_content(self, db_session, sample_document_data):
        """测试更新文档内容"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        original_version = document.version
        
        # 更新内容
        updated_doc = await service.update_document(
            document.id,
            content="新的内容"
        )
        
        assert updated_doc.version == original_version + 1
        assert updated_doc.content == "新的内容"
    
    @pytest.mark.asyncio
    async def test_update_document_not_found(self, db_session):
        """测试更新不存在的文档"""
        service = DocumentService(db_session)
        
        result = await service.update_document(
            "non-existent-id",
            title="新标题"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_document_soft(self, db_session, sample_document_data):
        """测试软删除文档"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 软删除
        result = await service.delete_document(document.id, soft_delete=True)
        
        assert result is True
        
        # 验证文档状态
        deleted_doc = await service.get_document(document.id)
        assert deleted_doc is not None
        assert deleted_doc.status == "archived"
    
    @pytest.mark.asyncio
    async def test_delete_document_hard(self, db_session, sample_document_data):
        """测试硬删除文档"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 硬删除
        result = await service.delete_document(document.id, soft_delete=False)
        
        assert result is True
        
        # 验证文档不存在
        deleted_doc = await service.get_document(document.id)
        assert deleted_doc is None
    
    @pytest.mark.asyncio
    async def test_publish_document(self, db_session, sample_document_data):
        """测试发布文档"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 发布文档
        published_doc = await service.publish_document(document.id)
        
        assert published_doc is not None
        assert published_doc.status == "published"
        assert published_doc.published_at is not None
    
    @pytest.mark.asyncio
    async def test_archive_document(self, db_session, sample_document_data):
        """测试归档文档"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 归档文档
        archived_doc = await service.archive_document(document.id)
        
        assert archived_doc is not None
        assert archived_doc.status == "archived"
    
    @pytest.mark.asyncio
    async def test_get_document_versions(self, db_session, sample_document_data):
        """测试获取文档版本历史"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 更新文档多次
        await service.update_document(document.id, title="版本2")
        await service.update_document(document.id, title="版本3")
        
        # 获取版本历史
        versions = await service.get_document_versions(document.id)
        
        assert len(versions) == 3
        assert versions[0].version == 3  # 最新版本在前
        assert versions[1].version == 2
        assert versions[2].version == 1
    
    @pytest.mark.asyncio
    async def test_restore_version(self, db_session, sample_document_data):
        """测试恢复文档版本"""
        service = DocumentService(db_session)
        
        # 创建文档
        document = await service.create_document(**sample_document_data)
        original_title = document.title
        
        # 更新文档
        await service.update_document(document.id, title="新标题")
        
        # 获取第一个版本
        versions = await service.get_document_versions(document.id)
        first_version = versions[-1]  # 最早的版本
        
        # 恢复到第一个版本
        restored_doc = await service.restore_version(document.id, first_version.id)
        
        assert restored_doc is not None
        assert restored_doc.title == original_title
        
        # 验证恢复后的版本历史
        versions_after = await service.get_document_versions(document.id)
        assert len(versions_after) == len(versions) + 1
    
    @pytest.mark.asyncio
    async def test_restore_version_invalid(self, db_session, sample_document_data):
        """测试恢复无效版本"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 尝试恢复不存在的版本
        result = await service.restore_version(document.id, "invalid-version-id")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, db_session, sample_document_data, sample_user_id):
        """测试获取文档统计"""
        service = DocumentService(db_session)
        
        # 创建不同状态和类型的文档
        await service.create_document(**sample_document_data)
        
        doc2 = await service.create_document(
            title="报告",
            content="报告内容",
            doc_type="report",
            creator_id=sample_user_id
        )
        await service.publish_document(doc2.id)
        
        # 获取统计
        stats = await service.get_statistics()
        
        assert "total" in stats
        assert "by_status" in stats
        assert "by_type" in stats
        assert stats["total"] >= 2
        assert "draft" in stats["by_status"]
        assert "published" in stats["by_status"]
    
    @pytest.mark.asyncio
    async def test_create_document_minimal(self, db_session, sample_user_id):
        """测试创建最小化文档（仅必需字段）"""
        service = DocumentService(db_session)
        
        document = await service.create_document(
            title="最小文档",
            content="内容",
            doc_type="general",
            creator_id=sample_user_id
        )
        
        assert document is not None
        assert document.tags == []
        assert document.attachments == []
        assert document.metadata == {}
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, db_session, sample_document_data):
        """测试并发更新文档版本号"""
        service = DocumentService(db_session)
        
        document = await service.create_document(**sample_document_data)
        
        # 多次更新
        for i in range(3):
            await service.update_document(
                document.id,
                content=f"更新内容 {i}"
            )
        
        # 验证最终版本号
        final_doc = await service.get_document(document.id)
        assert final_doc.version == 4  # 创建时1 + 3次更新
