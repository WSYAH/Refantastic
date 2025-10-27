"""启动后端服务"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger
from config import get_settings


def main():
    """启动服务主函数"""
    settings = get_settings()
    
    logger.info("=" * 50)
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")
    logger.info(f"数据库: {settings.DATABASE_TYPE}")
    
    # 检查并显示向量存储配置
    if hasattr(settings, 'VECTOR_STORE_TYPE'):
        logger.info(f"向量存储: {settings.VECTOR_STORE_TYPE}")
    else:
        logger.info("向量存储: 未配置")
    
    logger.info("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        access_log=settings.DEBUG
    )


if __name__ == "__main__":
    main()
