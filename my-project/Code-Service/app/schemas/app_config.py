"""
应用配置数据模式

包含应用配置和MCP配置的Pydantic模式
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AppConfigMcpDto(BaseModel):
    """MCP配置DTO"""
    url: str = Field(..., description="MCP服务URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头配置")


class AppConfigInput(BaseModel):
    """应用配置输入"""
    app_id: str = Field(..., description="应用ID")
    name: str = Field(..., description="应用名称")
    organization_name: str = Field(..., description="组织名称")
    repository_name: str = Field(..., description="仓库名称")
    allowed_domains: List[str] = Field(default_factory=list, description="允许的域名列表")
    enable_domain_validation: bool = Field(default=False, description="是否启用域名验证")
    description: str = Field(default="", description="应用描述")
    prompt: Optional[str] = Field(None, description="默认提示词")
    introduction: Optional[str] = Field(None, description="开场白")
    model: Optional[str] = Field(None, description="选择模型")
    recommended_questions: List[str] = Field(default_factory=list, description="设置推荐提问")
    mcps: List[AppConfigMcpDto] = Field(default_factory=list, description="MCP配置列表")


class AppConfigOutput(BaseModel):
    """应用配置输出"""
    app_id: str = Field(..., description="应用ID")
    name: str = Field(..., description="应用名称")
    is_enabled: bool = Field(default=True, description="是否启用")
    organization_name: str = Field(..., description="组织名称")
    repository_name: str = Field(..., description="仓库名称")
    allowed_domains: List[str] = Field(default_factory=list, description="允许的域名列表")
    enable_domain_validation: bool = Field(default=False, description="是否启用域名验证")
    description: str = Field(default="", description="应用描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    prompt: Optional[str] = Field(None, description="默认提示词")
    introduction: Optional[str] = Field(None, description="开场白")
    model: Optional[str] = Field(None, description="选择模型")
    recommended_questions: List[str] = Field(default_factory=list, description="设置推荐提问")
    mcps: List[AppConfigMcpDto] = Field(default_factory=list, description="MCP配置列表")


class DomainValidationRequest(BaseModel):
    """域名验证请求"""
    app_id: str = Field(..., description="应用ID")
    domain: str = Field(..., description="域名")


class DomainValidationResponse(BaseModel):
    """域名验证响应"""
    is_valid: bool = Field(..., description="是否有效")
    reason: Optional[str] = Field(None, description="原因")
    app_config: Optional[AppConfigOutput] = Field(None, description="应用配置") 