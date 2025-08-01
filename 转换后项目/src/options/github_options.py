import os
from typing import Optional
from pydantic import BaseSettings, Field


class GithubOptions(BaseSettings):
    """GitHub配置选项"""
    
    client_id: str = Field(default="", description="GitHub客户端ID")
    client_secret: str = Field(default="", description="GitHub客户端密钥")
    token: str = Field(default="", description="GitHub访问令牌")
    
    class Config:
        env_prefix = "GITHUB_"
    
    @classmethod
    def init_config(cls) -> "GithubOptions":
        """初始化配置"""
        # 从环境变量读取配置
        client_id = os.getenv("GITHUB_CLIENT_ID", "")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        token = os.getenv("GITHUB_TOKEN", "")
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            token=token
        )
    
    @classmethod
    def get_client_id(cls) -> str:
        """获取客户端ID"""
        return cls.init_config().client_id
    
    @classmethod
    def get_client_secret(cls) -> str:
        """获取客户端密钥"""
        return cls.init_config().client_secret
    
    @classmethod
    def get_token(cls) -> str:
        """获取访问令牌"""
        return cls.init_config().token 