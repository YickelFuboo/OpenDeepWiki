from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from src.models.base import BaseEntity


class AppConfig(BaseEntity):
    """应用配置模型"""
    __tablename__ = "app_configs"

    app_id = Column(String(100), nullable=False, unique=True, comment="应用ID")
    name = Column(String(200), nullable=False, comment="应用名称")
    organization_name = Column(String(100), nullable=False, comment="组织名称")
    repository_name = Column(String(100), nullable=False, comment="仓库名称")
    allowed_domains_json = Column(Text, nullable=True, comment="允许的域名JSON")
    enable_domain_validation = Column(Boolean, default=False, comment="是否启用域名验证")
    description = Column(Text, nullable=True, comment="应用描述")
    prompt = Column(Text, nullable=True, comment="默认提示词")
    introduction = Column(Text, nullable=True, comment="开场白")
    model = Column(String(100), nullable=True, comment="选择模型")
    recommended_questions_json = Column(Text, nullable=True, comment="推荐提问JSON")
    user_id = Column(String(36), nullable=False, comment="用户ID")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")

    # 关系
    mcps = relationship("AppConfigMcp", back_populates="app_config", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "name": self.name,
            "organization_name": self.organization_name,
            "repository_name": self.repository_name,
            "allowed_domains": self.get_allowed_domains(),
            "enable_domain_validation": self.enable_domain_validation,
            "description": self.description,
            "prompt": self.prompt,
            "introduction": self.introduction,
            "model": self.model,
            "recommended_questions": self.get_recommended_questions(),
            "user_id": self.user_id,
            "is_enabled": self.is_enabled,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_allowed_domains(self) -> list:
        """获取允许的域名列表"""
        if not self.allowed_domains_json:
            return []
        try:
            return json.loads(self.allowed_domains_json)
        except:
            return []

    def set_allowed_domains(self, domains: list):
        """设置允许的域名列表"""
        self.allowed_domains_json = json.dumps(domains)

    def get_recommended_questions(self) -> list:
        """获取推荐提问列表"""
        if not self.recommended_questions_json:
            return []
        try:
            return json.loads(self.recommended_questions_json)
        except:
            return []

    def set_recommended_questions(self, questions: list):
        """设置推荐提问列表"""
        self.recommended_questions_json = json.dumps(questions)


class AppConfigMcp(BaseEntity):
    """应用配置MCP模型"""
    __tablename__ = "app_config_mcps"

    app_config_id = Column(String(36), nullable=False, comment="应用配置ID")
    url = Column(String(500), nullable=False, comment="MCP服务URL")
    headers_json = Column(Text, nullable=True, comment="请求头JSON")

    # 关系
    app_config = relationship("AppConfig", back_populates="mcps")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "app_config_id": self.app_config_id,
            "url": self.url,
            "headers": self.get_headers(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_headers(self) -> dict:
        """获取请求头"""
        if not self.headers_json:
            return {}
        try:
            return json.loads(self.headers_json)
        except:
            return {}

    def set_headers(self, headers: dict):
        """设置请求头"""
        self.headers_json = json.dumps(headers) 