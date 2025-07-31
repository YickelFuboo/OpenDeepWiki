"""
JWT配置模块

处理JWT认证相关的配置
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

class JwtOptions(BaseModel):
    """JWT配置选项"""
    
    # JWT密钥
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT签名密钥"
    )
    
    # JWT算法
    algorithm: str = Field(
        default="HS256",
        description="JWT签名算法"
    )
    
    # 访问令牌过期时间（分钟）
    access_token_expire_minutes: int = Field(
        default=30,
        description="访问令牌过期时间（分钟）"
    )
    
    # 刷新令牌过期时间（天）
    refresh_token_expire_days: int = Field(
        default=7,
        description="刷新令牌过期时间（天）"
    )
    
    # 令牌颁发者
    issuer: str = Field(
        default="OpenDeepWiki",
        description="令牌颁发者"
    )
    
    # 令牌受众
    audience: str = Field(
        default="OpenDeepWiki-Users",
        description="令牌受众"
    )
    
    # 是否验证过期时间
    verify_expiration: bool = Field(
        default=True,
        description="是否验证令牌过期时间"
    )
    
    # 是否验证颁发者
    verify_issuer: bool = Field(
        default=True,
        description="是否验证令牌颁发者"
    )
    
    # 是否验证受众
    verify_audience: bool = Field(
        default=True,
        description="是否验证令牌受众"
    )

def get_jwt_options() -> JwtOptions:
    """获取JWT配置选项"""
    return JwtOptions(
        secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        issuer=os.getenv("JWT_ISSUER", "OpenDeepWiki"),
        audience=os.getenv("JWT_AUDIENCE", "OpenDeepWiki-Users"),
        verify_expiration=os.getenv("JWT_VERIFY_EXPIRATION", "true").lower() == "true",
        verify_issuer=os.getenv("JWT_VERIFY_ISSUER", "true").lower() == "true",
        verify_audience=os.getenv("JWT_VERIFY_AUDIENCE", "true").lower() == "true"
    )

# 全局JWT配置实例
jwt_options = get_jwt_options() 