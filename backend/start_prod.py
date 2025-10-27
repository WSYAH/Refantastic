"""生产环境启动脚本"""
import uvicorn
from config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print("=" * 60)
    print(f"启动 {settings.APP_NAME} - 生产环境")
    print("=" * 60)
    print(f"服务地址: http://localhost:8000")
    print(f"工作进程数: 4")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 多进程
        log_level="warning",
        access_log=True
    )
