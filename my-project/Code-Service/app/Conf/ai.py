"""
AI配置模块

处理AI相关的配置，包括OpenAI、Azure OpenAI、Anthropic等
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field

class OpenAIOptions(BaseModel):
    """OpenAI配置选项"""
    
    # OpenAI API密钥
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API密钥"
    )
    
    # OpenAI API基础URL
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API基础URL"
    )
    
    # 默认模型
    default_model: str = Field(
        default="gpt-4",
        description="默认使用的模型"
    )
    
    # 最大文件大小限制（MB）
    max_file_limit: int = Field(
        default=10,
        description="最大文件大小限制（MB）"
    )
    
    # 是否启用OpenAI
    enable_openai: bool = Field(
        default=True,
        description="是否启用OpenAI功能"
    )
    
    # 请求超时时间（秒）
    timeout: int = Field(
        default=60,
        description="请求超时时间（秒）"
    )
    
    # 最大重试次数
    max_retries: int = Field(
        default=3,
        description="最大重试次数"
    )

class AzureOpenAIOptions(BaseModel):
    """Azure OpenAI配置选项"""
    
    # Azure OpenAI API密钥
    api_key: Optional[str] = Field(
        default=None,
        description="Azure OpenAI API密钥"
    )
    
    # Azure OpenAI端点
    endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI端点"
    )
    
    # Azure OpenAI部署名称
    deployment_name: Optional[str] = Field(
        default=None,
        description="Azure OpenAI部署名称"
    )
    
    # 是否启用Azure OpenAI
    enable_azure_openai: bool = Field(
        default=False,
        description="是否启用Azure OpenAI功能"
    )

class AnthropicOptions(BaseModel):
    """Anthropic配置选项"""
    
    # Anthropic API密钥
    api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API密钥"
    )
    
    # Anthropic API基础URL
    base_url: str = Field(
        default="https://api.anthropic.com",
        description="Anthropic API基础URL"
    )
    
    # 默认模型
    default_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="默认使用的模型"
    )
    
    # 是否启用Anthropic
    enable_anthropic: bool = Field(
        default=False,
        description="是否启用Anthropic功能"
    )

class AIOptions(BaseModel):
    """AI配置总选项"""
    
    # OpenAI配置
    openai: OpenAIOptions = Field(
        default_factory=OpenAIOptions,
        description="OpenAI配置"
    )
    
    # Azure OpenAI配置
    azure_openai: AzureOpenAIOptions = Field(
        default_factory=AzureOpenAIOptions,
        description="Azure OpenAI配置"
    )
    
    # Anthropic配置
    anthropic: AnthropicOptions = Field(
        default_factory=AnthropicOptions,
        description="Anthropic配置"
    )
    
    # 默认AI提供商
    default_provider: str = Field(
        default="openai",
        description="默认AI提供商"
    )
    
    # 是否启用AI功能
    enable_ai: bool = Field(
        default=True,
        description="是否启用AI功能"
    )
    
    # 最大并发请求数
    max_concurrent_requests: int = Field(
        default=5,
        description="最大并发请求数"
    )
    
    # 请求队列大小
    request_queue_size: int = Field(
        default=100,
        description="请求队列大小"
    )

def get_ai_options() -> AIOptions:
    """获取AI配置选项"""
    return AIOptions(
        openai=OpenAIOptions(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4"),
            max_file_limit=int(os.getenv("OPENAI_MAX_FILE_LIMIT", "10")),
            enable_openai=os.getenv("ENABLE_OPENAI", "true").lower() == "true",
            timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        ),
        azure_openai=AzureOpenAIOptions(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            enable_azure_openai=os.getenv("ENABLE_AZURE_OPENAI", "false").lower() == "true"
        ),
        anthropic=AnthropicOptions(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-sonnet-20240229"),
            enable_anthropic=os.getenv("ENABLE_ANTHROPIC", "false").lower() == "true"
        ),
        default_provider=os.getenv("DEFAULT_AI_PROVIDER", "openai"),
        enable_ai=os.getenv("ENABLE_AI", "true").lower() == "true",
        max_concurrent_requests=int(os.getenv("AI_MAX_CONCURRENT_REQUESTS", "5")),
        request_queue_size=int(os.getenv("AI_REQUEST_QUEUE_SIZE", "100"))
    )

# 全局AI配置实例
ai_options = get_ai_options() 