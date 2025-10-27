"""开发环境启动脚本"""
import uvicorn
from config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print("=" * 70)
    print(f"🚀 启动 {settings.APP_NAME} - 开发环境")
    print("=" * 70)
    print(f"📍 服务地址:     http://localhost:8000")
    print(f"📚 API 文档:     http://localhost:8000/docs")
    print(f"🐛 调试模式:     {settings.DEBUG}")
    print("=" * 70)
    print("💡 提示：")
    print("   - 系统会自动检查并创建默认数据")
    print("   - 默认管理员: admin / admin123")
    print("   - 如需完整测试数据，请运行: python scripts/create_test_data.py")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开启热重载
        log_level="info"
    )
