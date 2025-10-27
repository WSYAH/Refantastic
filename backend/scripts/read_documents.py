"""读取并显示 documents 表中的所有记录"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from tabulate import tabulate

from models import Document, User
from core.database import AsyncSessionLocal, init_db


async def read_all_documents():
    """读取所有文档"""
    logger.info("=" * 80)
    logger.info("读取 documents 表")
    logger.info("=" * 80)
    
    async with AsyncSessionLocal() as session:
        # 获取文档总数
        count_result = await session.execute(select(func.count()).select_from(Document))
        total = count_result.scalar()
        
        logger.info(f"\n📊 文档总数: {total}\n")
        
        if total == 0:
            logger.warning("⚠️  documents 表为空")
            return
        
        # 查询所有文档
        result = await session.execute(
            select(Document).order_by(Document.created_at.desc())
        )
        documents = result.scalars().all()
        
        # 准备表格数据
        table_data = []
        for doc in documents:
            table_data.append([
                doc.id[:8] + "...",  # 显示ID前8位
                doc.title[:30] if len(doc.title) > 30 else doc.title,  # 标题最多30字符
                doc.doc_type,
                doc.status,
                doc.creator_id[:8] + "..." if doc.creator_id else "N/A",
                "是" if doc.is_public else "否",
                doc.version,
                doc.created_at.strftime("%Y-%m-%d %H:%M") if doc.created_at else "N/A"
            ])
        
        # 打印表格
        headers = ["ID", "标题", "类型", "状态", "创建人ID", "公开", "版本", "创建时间"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # 详细信息
        logger.info("\n" + "=" * 80)
        logger.info("📝 详细信息")
        logger.info("=" * 80)
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"\n【文档 {i}】")
            logger.info(f"  ID:          {doc.id}")
            logger.info(f"  标题:        {doc.title}")
            logger.info(f"  类型:        {doc.doc_type}")
            logger.info(f"  状态:        {doc.status}")
            logger.info(f"  文档编号:    {doc.doc_number or 'N/A'}")
            logger.info(f"  创建人ID:    {doc.creator_id}")
            logger.info(f"  模板ID:      {doc.template_id or 'N/A'}")
            logger.info(f"  是否公开:    {'是' if doc.is_public else '否'}")
            logger.info(f"  版本:        {doc.version}")
            logger.info(f"  标签:        {', '.join(doc.tags) if doc.tags else 'N/A'}")
            logger.info(f"  创建时间:    {doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else 'N/A'}")
            logger.info(f"  更新时间:    {doc.updated_at.strftime('%Y-%m-%d %H:%M:%S') if doc.updated_at else 'N/A'}")
            
            if doc.published_at:
                logger.info(f"  发布时间:    {doc.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 显示内容预览（前100字符）
            content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
            logger.info(f"  内容预览:    {content_preview}")
            logger.info("-" * 80)


async def read_documents_by_type():
    """按类型统计文档"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 按类型统计")
    logger.info("=" * 80 + "\n")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document.doc_type, func.count())
            .group_by(Document.doc_type)
        )
        
        type_stats = result.all()
        
        if not type_stats:
            logger.warning("没有文档数据")
            return
        
        table_data = [[doc_type, count] for doc_type, count in type_stats]
        headers = ["文档类型", "数量"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


async def read_documents_by_status():
    """按状态统计文档"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 按状态统计")
    logger.info("=" * 80 + "\n")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document.status, func.count())
            .group_by(Document.status)
        )
        
        status_stats = result.all()
        
        if not status_stats:
            logger.warning("没有文档数据")
            return
        
        status_map = {
            "draft": "草稿",
            "reviewing": "审核中",
            "approved": "已批准",
            "published": "已发布",
            "archived": "已归档"
        }
        
        table_data = [
            [status_map.get(status, status), count] 
            for status, count in status_stats
        ]
        headers = ["状态", "数量"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


async def read_document_by_id(doc_id: str):
    """根据ID读取单个文档的完整信息"""
    logger.info("=" * 80)
    logger.info(f"读取文档: {doc_id}")
    logger.info("=" * 80)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            logger.error(f"❌ 未找到ID为 {doc_id} 的文档")
            return
        
        logger.info(f"\n📄 文档详情")
        logger.info("-" * 80)
        logger.info(f"ID:           {doc.id}")
        logger.info(f"标题:         {doc.title}")
        logger.info(f"类型:         {doc.doc_type}")
        logger.info(f"状态:         {doc.status}")
        logger.info(f"文档编号:     {doc.doc_number or 'N/A'}")
        logger.info(f"创建人ID:     {doc.creator_id}")
        logger.info(f"审批人ID:     {doc.approver_id or 'N/A'}")
        logger.info(f"模板ID:       {doc.template_id or 'N/A'}")
        logger.info(f"是否公开:     {'是' if doc.is_public else '否'}")
        logger.info(f"版本:         {doc.version}")
        logger.info(f"标签:         {', '.join(doc.tags) if doc.tags else 'N/A'}")
        logger.info(f"创建时间:     {doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else 'N/A'}")
        logger.info(f"更新时间:     {doc.updated_at.strftime('%Y-%m-%d %H:%M:%S') if doc.updated_at else 'N/A'}")
        
        if doc.published_at:
            logger.info(f"发布时间:     {doc.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        logger.info("\n📝 完整内容:")
        logger.info("-" * 80)
        print(doc.content)
        logger.info("-" * 80)


async def main():
    """主函数"""
    import argparse
    
    # 首先初始化数据库（确保表存在）
    logger.info("🔧 初始化数据库...")
    await init_db()
    
    parser = argparse.ArgumentParser(description="读取 documents 表数据")
    parser.add_argument(
        "--id", 
        type=str, 
        help="指定文档ID查看详情"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="只显示统计信息"
    )
    
    args = parser.parse_args()
    
    if args.id:
        # 查看单个文档详情
        await read_document_by_id(args.id)
    elif args.stats:
        # 只显示统计
        await read_documents_by_type()
        await read_documents_by_status()
    else:
        # 显示所有文档
        await read_all_documents()
        await read_documents_by_type()
        await read_documents_by_status()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 读取完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
