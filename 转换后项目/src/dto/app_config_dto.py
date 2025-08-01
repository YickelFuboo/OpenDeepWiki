from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator
from datetime import datetime


class AppConfigMcpDto(BaseModel):
    """MCP配置DTO"""
    url: str = Field(..., description="MCP服务URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头配置")


class AppConfigInput(BaseModel):
    """应用配置输入DTO"""
    app_id: str = Field(..., description="应用ID")
    name: str = Field(..., description="应用名称")
    organization_name: str = Field(..., description="组织名称")
    repository_name: str = Field(..., description="仓库名称")
    allowed_domains: List[str] = Field(default_factory=list, description="允许的域名列表")
    enable_domain_validation: bool = Field(False, description="是否启用域名验证")
    description: str = Field("", description="应用描述")
    prompt: Optional[str] = Field(None, description="默认提示词")
    introduction: Optional[str] = Field(None, description="开场白")
    model: Optional[str] = Field(None, description="选择模型")
    recommended_questions: Optional[List[str]] = Field(None, description="推荐提问")
    mcps: List[AppConfigMcpDto] = Field(default_factory=list, description="MCP配置列表")

    @validator('app_id')
    def validate_app_id(cls, v):
        if not v or not v.strip():
            raise ValueError("应用ID不能为空")
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("应用名称不能为空")
        return v.strip()


class AppConfigOutput(BaseModel):
    """应用配置输出DTO"""
    app_id: str = Field(..., description="应用ID")
    name: str = Field(..., description="应用名称")
    is_enabled: bool = Field(True, description="是否启用")
    organization_name: str = Field(..., description="组织名称")
    repository_name: str = Field(..., description="仓库名称")
    allowed_domains: List[str] = Field(default_factory=list, description="允许的域名列表")
    enable_domain_validation: bool = Field(False, description="是否启用域名验证")
    description: str = Field("", description="应用描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    prompt: Optional[str] = Field(None, description="默认提示词")
    introduction: Optional[str] = Field(None, description="开场白")
    model: Optional[str] = Field(None, description="选择模型")
    recommended_questions: Optional[List[str]] = Field(None, description="推荐提问")
    mcps: List[AppConfigMcpDto] = Field(default_factory=list, description="MCP配置列表")


class DomainValidationRequest(BaseModel):
    """域名验证请求DTO"""
    app_id: str = Field(..., description="应用ID")
    domain: str = Field(..., description="域名")

    @validator('app_id')
    def validate_app_id(cls, v):
        if not v or not v.strip():
            raise ValueError("应用ID不能为空")
        return v.strip()

    @validator('domain')
    def validate_domain(cls, v):
        if not v or not v.strip():
            raise ValueError("域名不能为空")
        return v.strip()


class DomainValidationResponse(BaseModel):
    """域名验证响应DTO"""
    is_valid: bool = Field(..., description="是否有效")
    reason: Optional[str] = Field(None, description="原因")
    app_config: Optional[AppConfigOutput] = Field(None, description="应用配置") 