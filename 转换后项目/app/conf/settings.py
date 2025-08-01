import os
import secrets
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class OpenAISettings(BaseSettings):
    """OpenAI配置"""
    endpoint: str = Field(default="https://api.openai.com/v1", description="OpenAI API端点")
    chat_api_key: str = Field(default="", description="OpenAI聊天API密钥")
    chat_model: str = Field(default="gpt-4", description="聊天模型")
    analysis_model: str = Field(default="gpt-4", description="分析模型")
    deep_research_model: str = Field(default="gpt-4", description="深度研究模型")
    max_file_limit: int = Field(default=4000, description="最大文件限制")
    model_provider: str = Field(default="openai", description="模型提供者")
    
    class Config:
        env_prefix = "OPENAI_"


class Mem0Settings(BaseSettings):
    """Mem0配置"""
    enable_mem0: bool = Field(default=False, description="是否启用Mem0")
    mem0_api_key: str = Field(default="", description="Mem0 API密钥")
    mem0_endpoint: str = Field(default="https://api.mem0.ai", description="Mem0 API端点")
    
    class Config:
        env_prefix = "MEM0_"


class GithubSettings(BaseSettings):
    """GitHub配置"""
    client_id: str = Field(default="", description="GitHub客户端ID")
    client_secret: str = Field(default="", description="GitHub客户端密钥")
    token: str = Field(default="", description="GitHub访问令牌")
    
    class Config:
        env_prefix = "GITHUB_"


class GiteeSettings(BaseSettings):
    """Gitee配置"""
    client_id: str = Field(default="", description="Gitee客户端ID")
    client_secret: str = Field(default="", description="Gitee客户端密钥")
    token: str = Field(default="", description="Gitee访问令牌")
    
    class Config:
        env_prefix = "GITEE_"





class DocumentSettings(BaseSettings):
    """文档配置"""
    enable_code_dependency_analysis: bool = Field(default=True, description="启用代码依赖分析")
    enable_incremental_update: bool = Field(default=True, description="启用增量更新")
    enable_smart_filter: bool = Field(default=True, description="启用智能过滤")
    catalogue_format: str = Field(default="compact", description="目录结构格式")
    enable_warehouse_function_prompt_task: bool = Field(default=True, description="启用仓库功能提示任务")
    enable_warehouse_description_task: bool = Field(default=True, description="启用仓库描述任务")
    enable_file_commit: bool = Field(default=True, description="启用文件提交")
    enable_warehouse_commit: bool = Field(default=True, description="启用仓库提交")
    refine_and_enhance_quality: bool = Field(default=True, description="精炼并且提高质量")
    enable_code_compression: bool = Field(default=False, description="启用代码压缩")
    excluded_files: list = Field(default=[], description="排除的文件")
    excluded_folders: list = Field(default=[], description="排除的文件夹")
    
    class Config:
        env_prefix = "DOCUMENT_"


class GitSettings(BaseSettings):
    """Git配置选项"""
    path: str = Field(default="./repositories", description="Git仓库存储路径")
    username: str = Field(default="", description="Git用户名")
    password: str = Field(default="", description="Git密码")
    email: str = Field(default="koalawiki@example.com", description="Git邮箱")
    
    class Config:
        env_prefix = "GIT_"


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///./koalawiki.db", description="数据库URL")
    
    class Config:
        env_prefix = "DATABASE_"


class Settings(BaseSettings):
    """应用配置"""
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="主机地址")
    port: int = Field(default=8000, description="端口")
    
    openai: OpenAISettings = OpenAISettings()
    mem0: Mem0Settings = Mem0Settings()
    github: GithubSettings = GithubSettings()
    gitee: GiteeSettings = GiteeSettings()
    document: DocumentSettings = DocumentSettings()
    git: GitSettings = GitSettings()
    database: DatabaseSettings = DatabaseSettings()
    
    class Config:
        env_file = ".env"


# 创建全局设置实例
settings = Settings() 