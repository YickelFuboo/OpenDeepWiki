from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    db_type: str = "sqlite"
    db_connection_string: str = "sqlite:///./data/koalawiki.db"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 1440
    
    # AI模型配置
    model_provider: str = "OpenAI"
    chat_model: str = "gpt-4"
    analysis_model: str = "gpt-4"
    deep_research_model: str = "gpt-4"
    chat_api_key: str = "your-openai-api-key"
    endpoint: str = "https://api.openai.com/v1"
    
    # 仓库配置
    repositories_path: str = "./repositories"
    task_max_size_per_user: int = 5
    max_file_limit: int = 100
    update_interval: int = 7
    
    # 功能开关
    enable_smart_filter: bool = True
    enable_incremental_update: bool = True
    enable_code_dependency_analysis: bool = False
    enable_warehouse_commit: bool = True
    enable_file_commit: bool = True
    refine_and_enhance_quality: bool = True
    enable_warehouse_function_prompt_task: bool = True
    enable_warehouse_description_task: bool = True
    enable_code_compression: bool = False
    
    # 目录格式
    catalogue_format: str = "compact"
    
    # 语言设置
    language: str = "Chinese"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # 第三方登录配置
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    gitee_client_id: Optional[str] = None
    gitee_client_secret: Optional[str] = None
    
    # 文件上传配置
    upload_dir: str = "./uploads"
    max_upload_size: int = 104857600  # 100MB
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()


class DatabaseConfig:
    """数据库配置"""
    
    @staticmethod
    def get_database_url() -> str:
        """获取数据库连接URL"""
        return settings.db_connection_string
    
    @staticmethod
    def get_database_type() -> str:
        """获取数据库类型"""
        return settings.db_type


class JWTConfig:
    """JWT配置"""
    
    @staticmethod
    def get_secret_key() -> str:
        """获取JWT密钥"""
        return settings.jwt_secret_key
    
    @staticmethod
    def get_algorithm() -> str:
        """获取JWT算法"""
        return settings.jwt_algorithm
    
    @staticmethod
    def get_access_token_expire_minutes() -> int:
        """获取访问令牌过期时间（分钟）"""
        return settings.jwt_access_token_expire_minutes
    
    @staticmethod
    def get_refresh_token_expire_minutes() -> int:
        """获取刷新令牌过期时间（分钟）"""
        return settings.jwt_refresh_token_expire_minutes


class AIConfig:
    """AI配置"""
    
    @staticmethod
    def get_model_provider() -> str:
        """获取模型提供商"""
        return settings.model_provider
    
    @staticmethod
    def get_chat_model() -> str:
        """获取聊天模型"""
        return settings.chat_model
    
    @staticmethod
    def get_analysis_model() -> str:
        """获取分析模型"""
        return settings.analysis_model
    
    @staticmethod
    def get_deep_research_model() -> str:
        """获取深度研究模型"""
        return settings.deep_research_model
    
    @staticmethod
    def get_api_key() -> str:
        """获取API密钥"""
        return settings.chat_api_key
    
    @staticmethod
    def get_endpoint() -> str:
        """获取API端点"""
        return settings.endpoint


class RepositoryConfig:
    """仓库配置"""
    
    @staticmethod
    def get_repositories_path() -> str:
        """获取仓库存储路径"""
        return settings.repositories_path
    
    @staticmethod
    def get_task_max_size_per_user() -> int:
        """获取每用户最大任务数"""
        return settings.task_max_size_per_user
    
    @staticmethod
    def get_max_file_limit() -> int:
        """获取最大文件限制（MB）"""
        return settings.max_file_limit
    
    @staticmethod
    def get_update_interval() -> int:
        """获取更新间隔（天）"""
        return settings.update_interval


class FeatureConfig:
    """功能配置"""
    
    @staticmethod
    def is_smart_filter_enabled() -> bool:
        """是否启用智能过滤"""
        return settings.enable_smart_filter
    
    @staticmethod
    def is_incremental_update_enabled() -> bool:
        """是否启用增量更新"""
        return settings.enable_incremental_update
    
    @staticmethod
    def is_code_dependency_analysis_enabled() -> bool:
        """是否启用代码依赖分析"""
        return settings.enable_code_dependency_analysis
    
    @staticmethod
    def is_warehouse_commit_enabled() -> bool:
        """是否启用仓库提交"""
        return settings.enable_warehouse_commit
    
    @staticmethod
    def is_file_commit_enabled() -> bool:
        """是否启用文件提交"""
        return settings.enable_file_commit
    
    @staticmethod
    def is_refine_and_enhance_quality_enabled() -> bool:
        """是否启用精炼和提高质量"""
        return settings.refine_and_enhance_quality
    
    @staticmethod
    def is_warehouse_function_prompt_task_enabled() -> bool:
        """是否启用仓库功能提示任务"""
        return settings.enable_warehouse_function_prompt_task
    
    @staticmethod
    def is_warehouse_description_task_enabled() -> bool:
        """是否启用仓库描述任务"""
        return settings.enable_warehouse_description_task
    
    @staticmethod
    def is_code_compression_enabled() -> bool:
        """是否启用代码压缩"""
        return settings.enable_code_compression


class UploadConfig:
    """上传配置"""
    
    @staticmethod
    def get_upload_dir() -> str:
        """获取上传目录"""
        return settings.upload_dir
    
    @staticmethod
    def get_max_upload_size() -> int:
        """获取最大上传大小（字节）"""
        return settings.max_upload_size


class LogConfig:
    """日志配置"""
    
    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return settings.log_level
    
    @staticmethod
    def get_log_file() -> str:
        """获取日志文件路径"""
        return settings.log_file 