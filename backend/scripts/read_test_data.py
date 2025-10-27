"""读取并显示测试数据"""
import sys
import asyncio
from pathlib import Path
from typing import List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from loguru import logger

from models import (
    User, Role, Permission, UserRole, RolePermission,
    Template, TemplateVariable,
    Document, DocumentVersion,
    Workflow, WorkflowNode, WorkflowInstance, WorkflowTask,
    KnowledgeDocument, KnowledgeCategory,
    AuditLog
)

# 创建指向测试数据库的连接
DATA_DIR = Path(__file__).parent.parent / "data"
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/refantastic.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def read_users_and_roles(session: AsyncSession):
    """读取用户和角色数据"""
    logger.info("\n" + "=" * 60)
    logger.info("用户和角色信息")
    logger.info("=" * 60)
    
    # 读取用户
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    logger.info(f"\n总用户数: {len(users)}")
    for user in users:
        logger.info(f"\n用户: {user.username}")
        logger.info(f"  ID: {user.id}")
        logger.info(f"  邮箱: {user.email}")
        logger.info(f"  姓名: {user.full_name}")
        logger.info(f"  部门: {user.department}")
        logger.info(f"  职位: {user.position}")
        logger.info(f"  状态: {'激活' if user.is_active else '未激活'}")
        logger.info(f"  超级管理员: {'是' if user.is_superuser else '否'}")
        
        # 查询用户角色
        user_roles_result = await session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = user_roles_result.scalars().all()
        if user_roles:
            logger.info(f"  角色: {', '.join(r.name for r in user_roles)}")
    
    # 读取角色
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    
    logger.info(f"\n总角色数: {len(roles)}")
    for role in roles:
        logger.info(f"\n角色: {role.name} ({role.code})")
        logger.info(f"  描述: {role.description}")
        logger.info(f"  系统角色: {'是' if role.is_system else '否'}")
        
        # 查询角色权限
        perms_result = await session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        perms = perms_result.scalars().all()
        if perms:
            logger.info(f"  权限数量: {len(perms)}")
            logger.info(f"  权限: {', '.join(p.name for p in perms)}")


async def read_templates(session: AsyncSession):
    """读取模板数据"""
    logger.info("\n" + "=" * 60)
    logger.info("模板信息")
    logger.info("=" * 60)
    
    result = await session.execute(select(Template))
    templates = result.scalars().all()
    
    logger.info(f"\n总模板数: {len(templates)}")
    for template in templates:
        logger.info(f"\n模板: {template.name}")
        logger.info(f"  ID: {template.id}")
        logger.info(f"  类型: {template.doc_type}")
        logger.info(f"  分类: {template.category}")
        logger.info(f"  状态: {'激活' if template.is_active else '未激活'}")
        logger.info(f"  系统模板: {'是' if template.is_system else '否'}")
        
        # 查询模板变量
        vars_result = await session.execute(
            select(TemplateVariable)
            .where(TemplateVariable.template_id == template.id)
            .order_by(TemplateVariable.sort_order)
        )
        variables = vars_result.scalars().all()
        if variables:
            logger.info(f"  变量数量: {len(variables)}")
            for var in variables:
                required = "必填" if var.is_required else "可选"
                logger.info(f"    - {var.label} ({var.variable_name}): {var.variable_type} [{required}]")


async def read_documents(session: AsyncSession):
    """读取文档数据"""
    logger.info("\n" + "=" * 60)
    logger.info("文档信息")
    logger.info("=" * 60)
    
    result = await session.execute(select(Document))
    documents = result.scalars().all()
    
    logger.info(f"\n总文档数: {len(documents)}")
    for doc in documents:
        logger.info(f"\n文档: {doc.title}")
        logger.info(f"  ID: {doc.id}")
        logger.info(f"  文档编号: {doc.doc_number}")
        logger.info(f"  类型: {doc.doc_type}")
        logger.info(f"  状态: {doc.status}")
        logger.info(f"  标签: {', '.join(doc.tags) if doc.tags else '无'}")
        logger.info(f"  创建时间: {doc.created_at}")
        if (doc.published_at):
            logger.info(f"  发布时间: {doc.published_at}")
        
        # 查询文档版本
        versions_result = await session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.version)
        )
        versions = versions_result.scalars().all()
        logger.info(f"  版本数: {len(versions)}")


async def read_workflows(session: AsyncSession):
    """读取工作流数据"""
    logger.info("\n" + "=" * 60)
    logger.info("工作流信息")
    logger.info("=" * 60)
    
    result = await session.execute(select(Workflow))
    workflows = result.scalars().all()
    
    logger.info(f"\n总工作流数: {len(workflows)}")
    for workflow in workflows:
        logger.info(f"\n工作流: {workflow.name}")
        logger.info(f"  ID: {workflow.id}")
        logger.info(f"  文档类型: {workflow.doc_type}")
        logger.info(f"  描述: {workflow.description}")
        logger.info(f"  状态: {'激活' if workflow.is_active else '未激活'}")
        
        # 查询工作流节点
        nodes_result = await session.execute(
            select(WorkflowNode)
            .where(WorkflowNode.workflow_id == workflow.id)
            .order_by(WorkflowNode.sort_order)
        )
        nodes = nodes_result.scalars().all()
        logger.info(f"  节点数: {len(nodes)}")
        for node in nodes:
            logger.info(f"    {node.sort_order}. {node.name} ({node.node_type})")
            if node.approver_type and node.approver_id:
                logger.info(f"       审批者: {node.approver_type} - {node.approver_id}")


async def read_knowledge_base(session: AsyncSession):
    """读取知识库数据"""
    logger.info("\n" + "=" * 60)
    logger.info("知识库信息")
    logger.info("=" * 60)
    
    # 读取分类
    categories_result = await session.execute(
        select(KnowledgeCategory).order_by(KnowledgeCategory.sort_order)
    )
    categories = categories_result.scalars().all()
    
    logger.info(f"\n总分类数: {len(categories)}")
    for cat in categories:
        logger.info(f"\n分类: {cat.icon} {cat.name}")
        logger.info(f"  描述: {cat.description}")
        logger.info(f"  文档数: {cat.doc_count}")
    
    # 读取知识文档
    docs_result = await session.execute(select(KnowledgeDocument))
    docs = docs_result.scalars().all()
    
    logger.info(f"\n总知识文档数: {len(docs)}")
    for doc in docs:
        logger.info(f"\n文档: {doc.title}")
        logger.info(f"  类型: {doc.doc_type}")
        logger.info(f"  作者: {doc.author}")
        logger.info(f"  部门: {doc.department}")
        logger.info(f"  标签: {', '.join(doc.tags) if doc.tags else '无'}")
        logger.info(f"  质量分: {doc.quality_score}")
        logger.info(f"  浏览量: {doc.view_count}")
        logger.info(f"  状态: {doc.status}")


async def read_audit_logs(session: AsyncSession):
    """读取审计日志"""
    logger.info("\n" + "=" * 60)
    logger.info("审计日志")
    logger.info("=" * 60)
    
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
    )
    logs = result.scalars().all()
    
    logger.info(f"\n最近10条审计日志:")
    for log in logs:
        logger.info(f"\n时间: {log.created_at}")
        logger.info(f"  用户ID: {log.user_id}")
        logger.info(f"  操作: {log.action}")
        logger.info(f"  资源: {log.resource_type}")
        logger.info(f"  IP: {log.ip_address}")
        logger.info(f"  状态: {log.response_status}")


async def show_statistics(session: AsyncSession):
    """显示统计信息"""
    logger.info("\n" + "=" * 60)
    logger.info("数据统计")
    logger.info("=" * 60)
    
    # 统计各表记录数
    tables = [
        (User, "用户"),
        (Role, "角色"),
        (Permission, "权限"),
        (Template, "模板"),
        (Document, "文档"),
        (Workflow, "工作流"),
        (KnowledgeDocument, "知识文档"),
        (KnowledgeCategory, "知识分类"),
        (AuditLog, "审计日志")
    ]
    
    logger.info("")
    for model, name in tables:
        result = await session.execute(select(func.count()).select_from(model))
        count = result.scalar()
        logger.info(f"{name}: {count} 条记录")


async def main():
    """主函数"""
    logger.info("开始读取测试数据...")
    
    async with AsyncSessionLocal() as session:
        # 显示统计信息
        await show_statistics(session)
        
        # 读取各类数据
        await read_users_and_roles(session)
        await read_templates(session)
        await read_documents(session)
        await read_workflows(session)
        await read_knowledge_base(session)
        await read_audit_logs(session)
    
    logger.info("\n" + "=" * 60)
    logger.info("数据读取完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
