import uuid
import os
from typing import Optional
from pydantic import BaseSettings, Field


class JwtOptions(BaseSettings):
    """JWT配置选项"""
    
    name: str = Field(default="Jwt", description="配置名称")
    secret: str = Field(default="", description="密钥")
    issuer: str = Field(default="KoalaWiki", description="颁发者")
    audience: str = Field(default="KoalaWiki", description="接收者")
    expire_minutes: int = Field(default=60 * 24, description="过期时间（分钟）")
    refresh_expire_minutes: int = Field(default=60 * 24 * 7, description="刷新令牌过期时间（分钟）")
    
    class Config:
        env_prefix = "JWT_"
    
    def get_symmetric_security_key(self):
        """获取签名凭证"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        
        # 使用PBKDF2生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'koalawiki_salt',
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(self.secret.encode())
        return key
    
    @classmethod
    def init_config(cls) -> "JwtOptions":
        """初始化配置"""
        # 从环境变量读取配置
        secret = os.getenv("JWT_SECRET", "")
        issuer = os.getenv("JWT_ISSUER", "KoalaWiki")
        audience = os.getenv("JWT_AUDIENCE", "KoalaWiki")
        expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24小时
        refresh_expire_minutes = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTES", "10080"))  # 7天
        
        # 如果配置中没有设置密钥，则生成一个随机密钥
        if not secret:
            secret = f"{uuid.uuid4().hex}{uuid.uuid4().hex}"
        
        return cls(
            secret=secret,
            issuer=issuer,
            audience=audience,
            expire_minutes=expire_minutes,
            refresh_expire_minutes=refresh_expire_minutes
        )
    
    @classmethod
    def get_secret(cls) -> str:
        """获取密钥"""
        return cls.init_config().secret
    
    @classmethod
    def get_issuer(cls) -> str:
        """获取颁发者"""
        return cls.init_config().issuer
    
    @classmethod
    def get_audience(cls) -> str:
        """获取接收者"""
        return cls.init_config().audience
    
    @classmethod
    def get_expire_minutes(cls) -> int:
        """获取过期时间"""
        return cls.init_config().expire_minutes
    
    @classmethod
    def get_refresh_expire_minutes(cls) -> int:
        """获取刷新令牌过期时间"""
        return cls.init_config().refresh_expire_minutes 