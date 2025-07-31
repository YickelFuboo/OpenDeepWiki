"""
应用配置数据模型

包含应用配置和MCP配置的数据模型
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class AppConfig(Base):
    """应用配置模型"""
    __tablename__ = "app_configs"
    
    id = Column(String(36), primary_key=True, index=True)
    app_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    organization_name = Column(String(100), nullable=False)
    repository_name = Column(String(100), nullable=False)
    allowed_domains_json = Column(Text, default="[]")
    enable_domain_validation = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    introduction = Column(Text, nullable=True)
    model = Column(String(50), nullable=True)
    recommended_questions_json = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    is_enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    mcps = relationship("AppConfigMcp", back_populates="app_config", cascade="all, delete-orphan")
    
    @property
    def allowed_domains(self) -> list:
        """获取允许的域名列表"""
        try:
            return json.loads(self.allowed_domains_json or "[]")
        except:
            return []
    
    @property
    def recommended_questions(self) -> list:
        """获取推荐问题列表"""
        try:
            return json.loads(self.recommended_questions_json or "[]")
        except:
            return []


class AppConfigMcp(Base):
    """应用配置MCP模型"""
    __tablename__ = "app_config_mcps"
    
    id = Column(String(36), primary_key=True, index=True)
    app_config_id = Column(String(36), nullable=False, index=True)
    url = Column(String(255), nullable=False)
    headers_json = Column(Text, default="{}")
    
    # 关系
    app_config = relationship("AppConfig", back_populates="mcps")
    
    @property
    def headers(self) -> dict:
        """获取请求头字典"""
        try:
            return json.loads(self.headers_json or "{}")
        except:
            return {} 