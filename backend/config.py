from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用设置"""
    
    # 应用基础信息
    APP_NAME: str = "Refantastic 公文生成系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_TYPE: str = "sqlite"  # sqlite, mysql, postgresql
    DATABASE_URL: Optional[str] = None
    
    # SQLite 配置
    SQLITE_DB_PATH: str = "./data/refantastic.db"
    # PostgreSQL 配置
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/refantastic"
    
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "refantastic"

    VECTOR_STORE_PATH: str = "./data/vector_store"

    def set_DATABASE_URL(self) -> str:
        """根据数据库类型返回连接字符串"""
        if self.DATABASE_TYPE == "sqlite":
            # SQLite 使用 aiosqlite 驱动
            db_path = os.path.abspath(self.SQLITE_DB_PATH)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        else:
            return self.POSTGRES_URL
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = "chromadb"  # chromadb 或 milvus
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # 嵌入模型配置
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"  # 中文向量模型
    EMBEDDING_DIMENSION: int = 1024
    
    # LLM配置 (从config.yaml读取)
    LLM_TYPE: str = "openai"
    LLM_API_BASE: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # 其他配置
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "./logs"
    
    # JWT 配置
    SECRET_KEY: str = "a_random_jwt_key_for_my_gongwen_app"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    config: Dict[str, Any] = {}
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URL = self.set_DATABASE_URL()


def load_yaml_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载 YAML 配置文件
    
    Args:
        config_path: 配置文件路径,默认为 config/config.yaml
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return {}


def load_env_config(env_path: str = None) -> Dict[str, str]:
    """
    加载 .env 或 .config 文件
    
    Args:
        env_path: 环境文件路径,默认为 .config
    """
    if env_path is None:
        # 优先加载 .config,其次是 .env
        for filename in [".config", ".env"]:
            env_path = Path(__file__).parent / filename
            if env_path.exists():
                break
        else:
            return {}
    else:
        env_path = Path(env_path)
    
    if not env_path.exists():
        return {}
    
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as e:
        print(f"加载环境文件失败: {str(e)}")
    
    return env_vars


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    settings = Settings()
    
    # 加载 YAML 配置
    yaml_config = load_yaml_config()
    settings.config = yaml_config
    
    # 加载环境变量配置
    env_config = load_env_config()
    
    # 从 YAML 配置中提取数据库配置
    db_config = yaml_config.get("version_config", {}).get("db_config", {})
    if db_config:
        db_type = db_config.get("DB_TYPE", "sqlite").lower()
        settings.DATABASE_TYPE = db_type
        
        if db_type == "mysql":
            settings.MYSQL_HOST = db_config.get("DB_HOST")
            settings.MYSQL_PORT = db_config.get("DB_PORT", 3306)
            settings.MYSQL_USER = db_config.get("DB_USER")
            settings.MYSQL_PASSWORD = db_config.get("DB_PASSWORD")
            settings.MYSQL_DATABASE = db_config.get("DB_NAME")
            
            # 构建 MySQL URL
            settings.DATABASE_URL = (
                f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
                f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
            )
        elif db_type == "sqlite":
            settings.DATABASE_URL = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"
    
    # 从 YAML 和 .config 中提取 LLM 配置
    llm_config = yaml_config.get("version_config", {}).get("llm_config", {})
    big_model_config = yaml_config.get("version_config", {}).get("big_model", {})
    
    # 优先使用 .config 中的配置
    if "openai_api_base" in env_config:
        settings.LLM_API_BASE = env_config["openai_api_base"]
    elif "openai_api_base" in big_model_config:
        settings.LLM_API_BASE = big_model_config["openai_api_base"]
    
    
    if "openai_api_key" in env_config:
        settings.LLM_API_KEY = env_config["openai_api_key"]
    elif "key" in big_model_config:
        settings.LLM_API_KEY = big_model_config["key"]
    
    
    # LLM 类型
    if llm_config.get("llm_type"):
        settings.LLM_TYPE = llm_config["llm_type"]
    
    # 如果使用 deepseek,更新配置
    if settings.LLM_TYPE == "deepseek":
        if llm_config.get("llm_url"):
            settings.LLM_API_BASE = llm_config["llm_url"]
        if llm_config.get("llm_key"):
            settings.LLM_API_KEY = llm_config["llm_key"]
        if llm_config.get("llm_model_name"):
            settings.LLM_MODEL = llm_config["llm_model_name"]
    
    # 日志路径
    log_path = yaml_config.get("version_config", {}).get("log_path")
    if log_path:
        settings.LOG_PATH = log_path
    
    # 确保必要的目录存在
    Path(settings.LOG_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
    
    if settings.DATABASE_TYPE == "sqlite":
        Path(settings.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    return settings
