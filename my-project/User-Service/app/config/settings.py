"""
User-Service 配置管理模块
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    # 数据库类型
    db_type: str = Field(default="postgresql", env="DATABASE_TYPE")
    
    # PostgreSQL配置
    postgresql_host: str = Field(default="localhost", env="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, env="POSTGRESQL_PORT")
    postgresql_user: str = Field(default="postgres", env="POSTGRESQL_USER")
    postgresql_password: str = Field(default="", env="POSTGRESQL_PASSWORD")
    postgresql_database: str = Field(default="user_service", env="POSTGRESQL_DATABASE")
    
    # MySQL配置
    mysql_host: str = Field(default="localhost", env="MYSQL_HOST")
    mysql_port: int = Field(default=3306, env="MYSQL_PORT")
    mysql_user: str = Field(default="root", env="MYSQL_USER")
    mysql_password: str = Field(default="", env="MYSQL_PASSWORD")
    mysql_database: str = Field(default="user_service", env="MYSQL_DATABASE")
    
    # 连接池配置
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class S3Settings(BaseSettings):
    """S3存储配置"""
    
    region: str = Field(default="us-east-1", env="S3_REGION")
    endpoint_url: str = Field(default="", env="S3_ENDPOINT_URL")  # 必需，指定S3兼容服务的端点
    access_key_id: str = Field(default="", env="S3_ACCESS_KEY_ID")
    secret_access_key: str = Field(default="", env="S3_SECRET_ACCESS_KEY")
    use_ssl: bool = Field(default=True, env="S3_USE_SSL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class MinIOSettings(BaseSettings):
    """MinIO存储配置"""
    
    endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    secure: bool = Field(default=True, env="MINIO_SECURE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class LocalStorageSettings(BaseSettings):
    """本地存储配置"""
    
    upload_dir: str = Field(default="./user_avatar", env="LOCAL_UPLOAD_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class StorageSettings(BaseSettings):
    """存储配置"""
    
    storage_type: str = Field(default="minio", env="STORAGE_TYPE")
    
    s3: S3Settings = S3Settings()
    minio: MinIOSettings = MinIOSettings()
    local: LocalStorageSettings = LocalStorageSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class JWTSettings(BaseSettings):
    """JWT配置"""
    
    secret_key: str = Field(default="your-secret-key", env="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class SecuritySettings(BaseSettings):
    """安全配置"""
    
    # 密码策略
    min_password_length: int = Field(default=8, env="MIN_PASSWORD_LENGTH")
    require_uppercase: bool = Field(default=True, env="REQUIRE_UPPERCASE")
    require_lowercase: bool = Field(default=True, env="REQUIRE_LOWERCASE")
    require_digits: bool = Field(default=True, env="REQUIRE_DIGITS")
    require_special_chars: bool = Field(default=True, env="REQUIRE_SPECIAL_CHARS")
    
    # 登录限制
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(default=30, env="LOCKOUT_DURATION_MINUTES")
    
    # 会话配置
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class OAuthProviderConfig(BaseSettings):
    """单个OAuth提供商配置"""
    
    type: str = Field(default="oauth2")  # oauth2, oidc, github
    icon: str = Field(default="sso")  # github, sso, google, wechat, alipay
    display_name: str = Field(default="")
    client_id: str = Field(default="")
    client_secret: str = Field(default="")
    authorization_url: str = Field(default="")
    token_url: str = Field(default="")
    userinfo_url: str = Field(default="")
    issuer: str = Field(default="")  # 仅OIDC使用
    scope: str = Field(default="")  # 可配置的scope
    redirect_uri: str = Field(default="")
    is_active: bool = Field(default=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class OAuthSettings(BaseSettings):
    """OAuth配置 - 支持动态提供商"""
    
    # 启用OAuth功能
    enabled: bool = Field(default=True, env="OAUTH_ENABLED")
    
    # 默认配置（向后兼容）
    github_client_id: str = Field(default="", env="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", env="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(default="", env="GITHUB_REDIRECT_URI")
    
    google_client_id: str = Field(default="", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="", env="GOOGLE_REDIRECT_URI")
    
    wechat_app_id: str = Field(default="", env="WECHAT_APP_ID")
    wechat_app_secret: str = Field(default="", env="WECHAT_APP_SECRET")
    wechat_redirect_uri: str = Field(default="", env="WECHAT_REDIRECT_URI")
    
    # 支付宝 OAuth
    alipay_app_id: str = Field(default="", env="ALIPAY_APP_ID")
    alipay_private_key: str = Field(default="", env="ALIPAY_PRIVATE_KEY")
    alipay_public_key: str = Field(default="", env="ALIPAY_PUBLIC_KEY")
    alipay_redirect_uri: str = Field(default="", env="ALIPAY_REDIRECT_URI")
    
    # OIDC配置
    oidc_client_id: str = Field(default="", env="OIDC_CLIENT_ID")
    oidc_client_secret: str = Field(default="", env="OIDC_CLIENT_SECRET")
    oidc_redirect_uri: str = Field(default="", env="OIDC_REDIRECT_URI")
    oidc_issuer: str = Field(default="", env="OIDC_ISSUER")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class SMSSettings(BaseSettings):
    """短信服务配置"""
    
    provider: str = Field(default="aliyun", env="SMS_PROVIDER")
    access_key_id: str = Field(default="", env="SMS_ACCESS_KEY_ID")
    access_key_secret: str = Field(default="", env="SMS_ACCESS_KEY_SECRET")
    sign_name: str = Field(default="", env="SMS_SIGN_NAME")
    template_code: str = Field(default="", env="SMS_TEMPLATE_CODE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class EmailSettings(BaseSettings):
    """邮件服务配置"""
    
    host: str = Field(default="smtp.gmail.com", env="EMAIL_HOST")
    port: int = Field(default=587, env="EMAIL_PORT")
    username: str = Field(default="", env="EMAIL_USERNAME")
    password: str = Field(default="", env="EMAIL_PASSWORD")
    use_tls: bool = Field(default=True, env="EMAIL_USE_TLS")
    from_email: str = Field(default="", env="EMAIL_FROM")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """主配置类"""
    
    # 应用配置
    app_name: str = Field(default="User-Service", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="SERVICE_HOST")
    port: int = Field(default=8001, env="SERVICE_PORT")
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    jwt: JWTSettings = JWTSettings()
    security: SecuritySettings = SecuritySettings()
    oauth: OAuthSettings = OAuthSettings()
    sms: SMSSettings = SMSSettings()
    email: EmailSettings = EmailSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(f"加载配置: {_settings.app_name} v{_settings.app_version}")
    return _settings


def reload_settings():
    """重新加载配置"""
    global _settings
    _settings = None
    return get_settings() 