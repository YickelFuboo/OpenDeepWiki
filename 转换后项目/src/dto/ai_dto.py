from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """聊天消息DTO"""
    role: str = Field(..., description="消息角色 (user/assistant)")
    content: str = Field(..., description="消息内容")


class ResponsesInput(BaseModel):
    """AI响应输入DTO"""
    organization_name: str = Field(..., description="组织名称")
    name: str = Field(..., description="仓库名称")
    query: Optional[str] = Field(None, description="查询内容")
    messages: Optional[List[ChatMessage]] = Field(None, description="聊天消息列表")


class AIResponse(BaseModel):
    """AI响应DTO"""
    message: str = Field(..., description="响应消息")
    code: int = Field(..., description="响应代码")
    data: Optional[dict] = Field(None, description="响应数据")


class ProjectOverviewInput(BaseModel):
    """项目概述输入DTO"""
    repository_path: str = Field(..., description="仓库路径")
    catalog: str = Field(..., description="目录结构")
    git_repository: str = Field(..., description="Git仓库地址")
    branch: str = Field(..., description="分支名称")
    readme: str = Field(..., description="README内容")


class CodeAnalysisInput(BaseModel):
    """代码分析输入DTO"""
    repository_path: str = Field(..., description="仓库路径")
    file_paths: Optional[List[str]] = Field(None, description="要分析的文件路径列表")


class CodeAnalysisResult(BaseModel):
    """代码分析结果DTO"""
    tree_structure: str = Field(..., description="目录结构")
    analysis: str = Field(..., description="分析结果")
    file_info: Optional[dict] = Field(None, description="文件信息")
    dependencies: Optional[dict] = Field(None, description="依赖关系")


class PromptInput(BaseModel):
    """提示词输入DTO"""
    prompt_name: str = Field(..., description="提示词名称")
    parameters: dict = Field(default_factory=dict, description="提示词参数")
    model: Optional[str] = Field(None, description="使用的模型")


class PromptResult(BaseModel):
    """提示词结果DTO"""
    content: str = Field(..., description="生成的内容")
    usage: Optional[dict] = Field(None, description="使用统计")
    metadata: Optional[dict] = Field(None, description="元数据")


class FileAnalysisInput(BaseModel):
    """文件分析输入DTO"""
    file_paths: List[str] = Field(..., description="文件路径列表")
    analysis_type: str = Field(..., description="分析类型 (content/structure/dependencies)")


class FileAnalysisResult(BaseModel):
    """文件分析结果DTO"""
    file_info: dict = Field(..., description="文件信息")
    content_analysis: Optional[str] = Field(None, description="内容分析")
    structure_analysis: Optional[str] = Field(None, description="结构分析")
    dependency_analysis: Optional[str] = Field(None, description="依赖分析") 