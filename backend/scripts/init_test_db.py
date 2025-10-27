"""初始化测试数据库"""
import sys
import asyncio
import uuid
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.database import AsyncSessionLocal, init_db, engine
from models import Template, Document


async def drop_all_tables():
    """删除所有表"""
    from core.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("已删除所有表")


async def create_test_templates(session: AsyncSession):
    """创建测试模板"""
    templates = [
        Template(
            id=str(uuid.uuid4()),
            name="请示报告",
            doc_type="请示",
            category="请示",
            content="{{title}}\n\n{{department}}:\n\n{{content}}\n\n特此请示。\n\n{{date}}",
            variable_names=["title", "department", "content", "date"],
            description="标准请示报告模板",
            is_system=True
        ),
        Template(
            id=str(uuid.uuid4()),
            name="会议通知",
            doc_type="通知",
            category="通知",
            content="关于{{meeting_topic}}的通知\n\n各部门:\n\n定于{{meeting_time}}在{{meeting_location}}召开{{meeting_topic}}会议，请{{participants}}准时参加。",
            variable_names=["meeting_topic", "meeting_time", "meeting_location", "participants"],
            description="会议通知模板",
            is_system=True
        ),
        Template(
            id=str(uuid.uuid4()),
            name="工作总结",
            doc_type="总结",
            category="总结",
            content="{{period}}工作总结\n\n一、工作回顾\n{{review}}\n\n二、存在问题\n{{problems}}\n\n三、下步计划\n{{plans}}",
            variable_names=["period", "review", "problems", "plans"],
            description="工作总结模板",
            is_system=True
        ),
        Template(
            id=str(uuid.uuid4()),
            name="请假申请",
            doc_type="申请",
            category="申请",
            content="请假申请\n\n姓名：{{name}}\n部门：{{department}}\n请假类型：{{leave_type}}\n请假时间：{{start_date}} 至 {{end_date}}\n请假事由：{{reason}}\n\n申请人：{{name}}\n日期：{{apply_date}}",
            variable_names=["name", "department", "leave_type", "start_date", "end_date", "reason", "apply_date"],
            description="请假申请模板",
            is_system=True
        )
    ]
    
    # 保存模板 ID 用于后续创建文档
    template_ids = [t.id for t in templates]
    
    for template in templates:
        session.add(template)
    
    await session.commit()
    logger.info(f"创建了 {len(templates)} 个测试模板")
    
    return template_ids


async def create_test_documents(session: AsyncSession, template_ids: list):
    """创建测试文档"""
    documents = [
        Document(
            id=str(uuid.uuid4()),
            title="关于采购办公设备的请示",
            doc_type="请示",
            content="关于采购办公设备的请示\n\n行政部:\n\n因业务发展需要，拟采购电脑10台，预算5万元。\n\n特此请示。\n\n2024年1月15日",
            template_id=template_ids[0] if template_ids else None,
            status="draft",
            creator_id=str(uuid.uuid4())  # 临时创建者ID
        ),
        Document(
            id=str(uuid.uuid4()),
            title="2024年第一季度工作总结",
            doc_type="总结",
            content="2024年第一季度工作总结\n\n一、工作回顾\n完成了各项既定目标...\n\n二、存在问题\n部分工作进度有所滞后...\n\n三、下步计划\n继续推进重点项目...",
            template_id=template_ids[2] if len(template_ids) > 2 else None,
            status="published",
            creator_id=str(uuid.uuid4())  # 临时创建者ID
        )
    ]
    
    for document in documents:
        session.add(document)
    
    await session.commit()
    logger.info(f"创建了 {len(documents)} 个测试文档")


async def main():
    """主函数"""
    logger.info("开始初始化测试数据库...")
    
    # 删除所有表（重新开始）
    await drop_all_tables()
    
    # 初始化数据库结构
    await init_db()
    
    # 创建测试数据
    async with AsyncSessionLocal() as session:
        template_ids = await create_test_templates(session)
        await create_test_documents(session, template_ids)
    
    logger.info("测试数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
