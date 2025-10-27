import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Template, Document


class TestTemplateModel:
    """模板模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_template(self, db_session: AsyncSession):
        """测试创建模板"""
        template = Template(
            name="测试模板",
            category="测试",
            content="测试内容 {{variable}}",
            variables=["variable"]
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        assert template.id is not None
        assert template.name == "测试模板"
        assert template.is_active is True
    
    @pytest.mark.asyncio
    async def test_query_template(self, db_session: AsyncSession):
        """测试查询模板"""
        # 创建模板
        template = Template(
            name="查询测试",
            category="测试",
            content="内容",
            variables=[]
        )
        db_session.add(template)
        await db_session.commit()
        
        # 查询
        result = await db_session.execute(
            select(Template).where(Template.name == "查询测试")
        )
        found_template = result.scalar_one_or_none()
        
        assert found_template is not None
        assert found_template.name == "查询测试"


class TestDocumentModel:
    """文档模型测试"""
    
    @pytest.mark.asyncio
    async def test_create_document(self, db_session: AsyncSession):
        """测试创建文档"""
        # 先创建模板
        template = Template(
            name="文档测试模板",
            category="测试",
            content="内容",
            variables=[]
        )
        db_session.add(template)
        await db_session.commit()
        
        # 创建文档
        document = Document(
            title="测试文档",
            content="文档内容",
            template_id=template.id,
            status="draft"
        )
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        assert document.id is not None
        assert document.title == "测试文档"
        assert document.template_id == template.id
    
    @pytest.mark.asyncio
    async def test_document_template_relationship(self, db_session: AsyncSession):
        """测试文档和模板的关系"""
        # 创建模板
        template = Template(
            name="关系测试模板",
            category="测试",
            content="内容",
            variables=[]
        )
        db_session.add(template)
        await db_session.commit()
        
        # 创建文档
        document = Document(
            title="关系测试文档",
            content="内容",
            template_id=template.id,
            status="draft"
        )
        db_session.add(document)
        await db_session.commit()
        
        # 查询文档并加载关联的模板
        result = await db_session.execute(
            select(Document).where(Document.id == document.id)
        )
        found_document = result.scalar_one()
        
        # 加载关联的模板
        await db_session.refresh(found_document, ["template"])
        
        assert found_document.template is not None
        assert found_document.template.name == "关系测试模板"
