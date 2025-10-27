"""初始化默认数据脚本 - 用于快速设置基础数据"""
import sys
import asyncio
import uuid
from pathlib import Path
import bcrypt
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func
from loguru import logger

from models import User, Template, TemplateVariable, Workflow, WorkflowNode, Document
from core.database import Base

# 使用主数据库
from core.database import engine, AsyncSessionLocal


async def init_default_users(session: AsyncSession):
    """初始化默认用户"""
    logger.info("检查用户数据...")
    
    user_count = await session.execute(select(func.count()).select_from(User))
    if user_count.scalar() > 0:
        logger.info("用户表已有数据，跳过")
        return
    
    logger.info("创建默认用户...")
    
    # 哈希密码
    password_bytes = "admin123".encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # 创建管理员
    admin = User(
        id="123",
        username="admin",
        email="admin@refantastic.com",
        password_hash=hashed.decode('utf-8'),
        full_name="系统管理员",
        department="系统",
        position="管理员",
        is_active=True,
        is_superuser=True
    )
    session.add(admin)
    
    # 创建测试用户
    test_password = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt())
    test_user = User(
        id=str(uuid.uuid4()),
        username="test",
        email="test@refantastic.com",
        password_hash=test_password.decode('utf-8'),
        full_name="测试用户",
        department="测试部",
        position="员工",
        is_active=True,
        is_superuser=False
    )
    session.add(test_user)
    
    await session.commit()
    logger.info("✅ 创建了 2 个默认用户")
    logger.info("   - admin / admin123 (管理员)")
    logger.info("   - test / test123 (普通用户)")


async def init_default_templates(session: AsyncSession):
    """初始化默认模板"""
    logger.info("检查模板数据...")
    
    template_count = await session.execute(select(func.count()).select_from(Template))
    if template_count.scalar() > 0:
        logger.info("模板表已有数据，跳过")
        return
    
    logger.info("创建默认模板...")
    
    # 获取管理员ID
    admin_result = await session.execute(
        select(User).where(User.is_superuser == True).limit(1)
    )
    admin = admin_result.scalar_one_or_none()
    if not admin:
        logger.error("找不到管理员用户，请先创建用户")
        return
    
    templates_data = [
        {
            "name": "通用文档模板",
            "doc_type": "通用",
            "category": "默认模板",
            "content": "{{title}}\n\n{{content}}\n\n{{department}}\n{{date}}",
            "variables": [
                {"name": "title", "type": "text", "label": "标题"},
                {"name": "content", "type": "text", "label": "内容"},
                {"name": "department", "type": "text", "label": "部门"},
                {"name": "date", "type": "date", "label": "日期"}
            ]
        },
        {
            "name": "通知模板",
            "doc_type": "通知",
            "category": "默认模板",
            "content": "{{title}}\n\n{{recipient}}：\n\n{{content}}\n\n{{department}}\n{{date}}",
            "variables": [
                {"name": "title", "type": "text", "label": "标题"},
                {"name": "recipient", "type": "text", "label": "收件人"},
                {"name": "content", "type": "text", "label": "内容"},
                {"name": "department", "type": "text", "label": "发文部门"},
                {"name": "date", "type": "date", "label": "日期"}
            ]
        },
        {
            "name": "申请模板",
            "doc_type": "申请",
            "category": "默认模板",
            "content": "{{title}}\n\n申请人：{{applicant}}\n部门：{{department}}\n\n申请内容：\n{{content}}\n\n{{date}}",
            "variables": [
                {"name": "title", "type": "text", "label": "标题"},
                {"name": "applicant", "type": "text", "label": "申请人"},
                {"name": "department", "type": "text", "label": "部门"},
                {"name": "content", "type": "text", "label": "申请内容"},
                {"name": "date", "type": "date", "label": "日期"}
            ]
        }
    ]
    
    for template_data in templates_data:
        template = Template(
            id=str(uuid.uuid4()),
            name=template_data["name"],
            doc_type=template_data["doc_type"],
            category=template_data["category"],
            content=template_data["content"],
            variable_names=[v["name"] for v in template_data["variables"]],
            description=f"{template_data['name']} - 系统默认",
            is_system=True,
            is_active=True,
            creator_id=admin.id
        )
        session.add(template)
        await session.flush()
        
        # 创建模板变量
        for idx, var_data in enumerate(template_data["variables"]):
            var = TemplateVariable(
                id=str(uuid.uuid4()),
                template_id=template.id,
                variable_name=var_data["name"],
                variable_type=var_data["type"],
                label=var_data["label"],
                is_required=True,
                sort_order=idx
            )
            session.add(var)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(templates_data)} 个默认模板")


async def init_default_workflows(session: AsyncSession):
    """初始化默认工作流"""
    logger.info("检查工作流数据...")
    
    workflow_count = await session.execute(select(func.count()).select_from(Workflow))
    if workflow_count.scalar() > 0:
        logger.info("工作流表已有数据，跳过")
        return
    
    logger.info("创建默认工作流...")
    
    workflows_data = [
        {
            "name": "简单审批流程",
            "doc_type": "通用",
            "description": "适用于一般文档的简单审批流程",
            "nodes": [
                {"name": "开始", "type": "start", "order": 1},
                {"name": "审批", "type": "approval", "order": 2, "approver_type": "role", "approver_id": "manager"},
                {"name": "完成", "type": "end", "order": 3}
            ]
        },
        {
            "name": "通知发布流程",
            "doc_type": "通知",
            "description": "通知文档的发布流程",
            "nodes": [
                {"name": "开始", "type": "start", "order": 1},
                {"name": "审核", "type": "approval", "order": 2, "approver_type": "role", "approver_id": "manager"},
                {"name": "发布", "type": "end", "order": 3}
            ]
        },
        {
            "name": "申请审批流程",
            "doc_type": "申请",
            "description": "申请文档的审批流程",
            "nodes": [
                {"name": "提交", "type": "start", "order": 1},
                {"name": "部门审批", "type": "approval", "order": 2, "approver_type": "role", "approver_id": "manager"},
                {"name": "完成", "type": "end", "order": 3}
            ]
        }
    ]
    
    for workflow_data in workflows_data:
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=workflow_data["name"],
            doc_type=workflow_data["doc_type"],
            description=workflow_data["description"],
            is_active=True,
            config={"auto_notify": True, "timeout_days": 3}
        )
        session.add(workflow)
        await session.flush()
        
        # 创建工作流节点
        for node_data in workflow_data["nodes"]:
            node = WorkflowNode(
                id=str(uuid.uuid4()),
                workflow_id=workflow.id,
                name=node_data["name"],
                node_type=node_data["type"],
                sort_order=node_data["order"],
                approver_type=node_data.get("approver_type"),
                approver_id=node_data.get("approver_id")
            )
            session.add(node)
    
    await session.commit()
    logger.info(f"✅ 创建了 {len(workflows_data)} 个默认工作流")


async def init_default_documents(session: AsyncSession):
    """初始化默认文档"""
    logger.info("检查文档数据...")
    
    doc_count = await session.execute(select(func.count()).select_from(Document))
    count = doc_count.scalar()
    logger.info(f"当前文档表记录数: {count}")
    
    if count > 0:
        logger.info("文档表已有数据，跳过")
        return
    
    logger.info("创建默认文档...")
    
    # 直接使用管理员 ID
    admin_id = "123"
    
    # 获取测试用户ID（如果存在）
    test_result = await session.execute(
        select(User.id).where(User.username == "test")
    )
    test_user_id = test_result.scalar_one_or_none()
    
    # 获取默认模板ID（如果存在）
    template_result = await session.execute(
        select(Template.id).where(Template.name == "通用文档模板")
    )
    template_id = template_result.scalar_one_or_none()
    
    if template_id:
        logger.info(f"找到默认模板: {template_id}")
    
    documents_data = [
        {
            "title": "公司年度工作总结",
            "content": """# 2024年度工作总结

## 一、工作概况
本年度公司在各项业务上取得了显著成绩，员工满意度持续提升。

## 二、主要成果
1. 营业收入增长30%
2. 新产品研发成功上线3款
3. 客户满意度达到95%

## 三、下一步计划
继续保持发展势头，深化改革创新。

行政部
2024-12-20""",
            "doc_type": "通用",
            "status": "published",
            "creator_id": admin_id,
            "template_id": template_id,
            "is_public": True
        },
        {
            "title": "员工培训通知",
            "content": """# 员工培训通知

各部门：

为提升员工专业技能，公司决定组织本月员工培训活动。

**培训时间：** 2024年12月25日 14:00-17:00
**培训地点：** 公司会议室
**参加人员：** 全体员工

请各部门按时组织员工参加。

人力资源部
2024-12-20""",
            "doc_type": "通知",
            "status": "published",
            "creator_id": admin_id,
            "is_public": True
        },
        {
            "title": "设备采购申请",
            "content": """# 设备采购申请

**申请人：** 张三
**部门：** 技术部
**申请日期：** 2024-12-20

## 申请内容
申请采购开发服务器5台，用于新项目开发环境搭建。

## 预算说明
预计费用：50,000元
资金来源：年度IT预算

技术部
2024-12-20""",
            "doc_type": "申请",
            "status": "reviewing",
            "creator_id": test_user_id if test_user_id else admin_id,
            "is_public": False
        },
        {
            "title": "会议纪要 - 季度总结会",
            "content": """# 2024年Q4季度总结会议纪要

**会议时间：** 2024-12-18 10:00-12:00
**会议地点：** 大会议室
**参会人员：** 各部门负责人

## 会议内容
1. 回顾本季度工作完成情况
2. 讨论下季度工作计划
3. 表彰优秀员工

## 决议事项
- 调整下季度销售目标
- 增加市场推广预算
- 启动新产品开发项目

行政部
2024-12-18""",
            "doc_type": "通用",
            "status": "approved",
            "creator_id": admin_id,
            "is_public": True
        },
        {
            "title": "休假申请",
            "content": """# 休假申请

**申请人：** 李四
**部门：** 销售部
**申请日期：** 2024-12-20

## 休假信息
**休假类型：** 年假
**休假时间：** 2024-12-25 至 2024-12-27（共3天）
**休假原因：** 个人事务

已做好工作交接安排。

销售部 李四
2024-12-20""",
            "doc_type": "申请",
            "status": "draft",
            "creator_id": test_user_id if test_user_id else admin_id,
            "is_public": False
        }
    ]
    
    created_docs = []
    for idx, doc_data in enumerate(documents_data, 1):
        doc = Document(
            id=str(uuid.uuid4()),
            title=doc_data["title"],
            content=doc_data["content"],
            doc_type=doc_data["doc_type"],
            doc_number=f"DOC{datetime.now().strftime('%Y%m%d')}{idx:04d}",
            status=doc_data["status"],
            creator_id=doc_data["creator_id"],
            template_id=doc_data.get("template_id"),
            is_public=doc_data.get("is_public", False),
            version=1,
            tags=["默认", "示例"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 如果是已发布的文档，设置发布时间
        if doc.status == "published":
            doc.published_at = datetime.utcnow()
        
        session.add(doc)
        created_docs.append(doc)
        logger.info(f"添加文档: {doc.title} (ID: {doc.id}, Status: {doc.status}, Creator: {doc.creator_id})")
    
    # 提交到数据库
    try:
        await session.commit()
        logger.info(f"✅ 成功创建了 {len(created_docs)} 个默认文档")
        
        # 验证是否真的插入成功
        verify_count = await session.execute(select(func.count()).select_from(Document))
        final_count = verify_count.scalar()
        logger.info(f"验证: 文档表现在有 {final_count} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 提交文档数据失败: {str(e)}")
        await session.rollback()
        raise


async def ensure_default_data():
    """确保默认数据存在（应用启动时调用）"""
    logger.info("检查默认数据...")
    
    # 导入放在函数内部，避免循环引用
    from core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # 检查是否需要初始化数据
        user_count = await session.execute(select(func.count()).select_from(User))
        
        if user_count.scalar() == 0:
            logger.warning("检测到空数据库，开始初始化默认数据...")
            await init_default_users(session)
            await init_default_templates(session)
            await init_default_workflows(session)
            await init_default_documents(session)
            logger.info("✅ 默认数据初始化完成")
        else:
            logger.info("✅ 数据库已有数据，跳过初始化")


async def main():
    """主函数 - 用于手动执行初始化"""
    logger.info("=" * 60)
    logger.info("初始化默认数据")
    logger.info("=" * 60)
    
    # 导入放在函数内部，避免循环引用
    from core.database import engine, AsyncSessionLocal, Base
    
    # 确保数据库表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # 初始化各类默认数据
        await init_default_users(session)
        await init_default_templates(session)
        await init_default_workflows(session)
        await init_default_documents(session)
    
    logger.info("=" * 60)
    logger.info("✅ 默认数据初始化完成！")
    logger.info("=" * 60)
    logger.info("默认账号:")
    logger.info("  管理员: admin / admin123")
    logger.info("  测试用户: test / test123")
    logger.info("=" * 60)
    logger.info("默认数据:")
    logger.info("  - 3个模板（通用文档、通知、申请）")
    logger.info("  - 3个工作流程")
    logger.info("  - 5个示例文档")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
