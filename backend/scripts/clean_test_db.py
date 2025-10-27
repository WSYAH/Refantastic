"""清理测试数据库"""
import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from core.database import engine, Base


async def main():
    """清理数据库"""
    logger.info("开始清理测试数据库...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("所有表已删除")
        
        await conn.run_sync(Base.metadata.create_all)
        logger.info("重新创建表结构")
    
    logger.info("测试数据库清理完成！")


if __name__ == "__main__":
    asyncio.run(main())
