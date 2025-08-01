import os
from typing import Optional
from pydantic import BaseSettings, Field


class OpenAIOptions(BaseSettings):
    """OpenAI配置选项"""
    
    # 模型配置
    chat_model: str = Field(default="", description="ChatGPT模型")
    analysis_model: str = Field(default="", description="分析模型")
    deep_research_model: str = Field(default="", description="深度研究模型")
    
    # API配置
    chat_api_key: str = Field(default="", description="ChatGPT API密钥")
    endpoint: str = Field(default="", description="API地址")
    model_provider: str = Field(default="OpenAI", description="模型提供商")
    
    # 限制配置
    max_file_limit: int = Field(default=10, description="最大文件限制")
    
    # Mem0配置
    enable_mem0: bool = Field(default=False, description="启用Mem0")
    mem0_api_key: str = Field(default="", description="Mem0 API密钥")
    mem0_endpoint: str = Field(default="", description="Mem0端点")
    
    class Config:
        env_prefix = "OPENAI_"
    
    @classmethod
    def init_config(cls) -> "OpenAIOptions":
        """初始化配置"""
        # 从环境变量读取配置
        chat_model = os.getenv("CHAT_MODEL", "") or os.getenv("OPENAI_CHAT_MODEL", "")
        analysis_model = os.getenv("ANALYSIS_MODEL", "") or os.getenv("OPENAI_ANALYSIS_MODEL", "")
        chat_api_key = os.getenv("CHAT_API_KEY", "") or os.getenv("OPENAI_CHAT_API_KEY", "")
        endpoint = os.getenv("ENDPOINT", "") or os.getenv("OPENAI_ENDPOINT", "")
        model_provider = os.getenv("MODEL_PROVIDER", "") or os.getenv("OPENAI_MODEL_PROVIDER", "OpenAI")
        deep_research_model = os.getenv("DEEP_RESEARCH_MODEL", "") or os.getenv("OPENAI_DEEP_RESEARCH_MODEL", "")
        max_file_limit = int(os.getenv("MAX_FILE_LIMIT", "10"))
        enable_mem0 = os.getenv("ENABLE_MEM0", "false").lower() == "true"
        mem0_api_key = os.getenv("MEM0_API_KEY", "") or os.getenv("OPENAI_MEM0_API_KEY", "")
        mem0_endpoint = os.getenv("MEM0_ENDPOINT", "") or os.getenv("OPENAI_MEM0_ENDPOINT", "")
        
        # 验证必需参数
        if not chat_model:
            raise ValueError("ChatModel is empty")
        
        if not chat_api_key:
            raise ValueError("ChatApiKey is empty")
        
        if not endpoint:
            raise ValueError("Endpoint is empty")
        
        # 设置默认值
        if not deep_research_model:
            deep_research_model = chat_model
        
        if not analysis_model:
            analysis_model = chat_model
        
        if not model_provider:
            model_provider = "OpenAI"
        
        # Mem0验证
        if enable_mem0 and not mem0_endpoint:
            raise ValueError("Mem0Endpoint is empty or not set")
        
        return cls(
            chat_model=chat_model,
            analysis_model=analysis_model,
            chat_api_key=chat_api_key,
            endpoint=endpoint,
            model_provider=model_provider,
            deep_research_model=deep_research_model,
            max_file_limit=max_file_limit,
            enable_mem0=enable_mem0,
            mem0_api_key=mem0_api_key,
            mem0_endpoint=mem0_endpoint
        )
    
    @classmethod
    def get_chat_model(cls) -> str:
        """获取ChatGPT模型"""
        return cls.init_config().chat_model
    
    @classmethod
    def get_analysis_model(cls) -> str:
        """获取分析模型"""
        return cls.init_config().analysis_model
    
    @classmethod
    def get_chat_api_key(cls) -> str:
        """获取ChatGPT API密钥"""
        return cls.init_config().chat_api_key
    
    @classmethod
    def get_endpoint(cls) -> str:
        """获取API地址"""
        return cls.init_config().endpoint
    
    @classmethod
    def get_model_provider(cls) -> str:
        """获取模型提供商"""
        return cls.init_config().model_provider
    
    @classmethod
    def get_deep_research_model(cls) -> str:
        """获取深度研究模型"""
        return cls.init_config().deep_research_model
    
    @classmethod
    def get_max_file_limit(cls) -> int:
        """获取最大文件限制"""
        return cls.init_config().max_file_limit
    
    @classmethod
    def get_enable_mem0(cls) -> bool:
        """获取是否启用Mem0"""
        return cls.init_config().enable_mem0
    
    @classmethod
    def get_mem0_api_key(cls) -> str:
        """获取Mem0 API密钥"""
        return cls.init_config().mem0_api_key
    
    @classmethod
    def get_mem0_endpoint(cls) -> str:
        """获取Mem0端点"""
        return cls.init_config().mem0_endpoint 