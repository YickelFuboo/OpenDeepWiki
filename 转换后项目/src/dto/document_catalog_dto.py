from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DocumentCatalogTreeItem(BaseModel):
    """文档目录树项"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    url: str = Field(..., description="目录URL")
    description: Optional[str] = Field(None, description="目录描述")
    parent_id: Optional[str] = Field(None, description="目录父级ID")
    order: int = Field(0, description="当前目录排序")
    is_completed: bool = Field(False, description="是否处理完成")
    prompt: Optional[str] = Field(None, description="提示词")
    children: List['DocumentCatalogTreeItem'] = Field(default_factory=list, description="子目录")


class DocumentCatalogResponse(BaseModel):
    """文档目录响应"""
    items: List[DocumentCatalogTreeItem] = Field(default_factory=list, description="目录树")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")
    description: Optional[str] = Field(None, description="文档描述")
    progress: int = Field(0, description="处理进度")
    git: str = Field(..., description="Git地址")
    branchs: List[str] = Field(default_factory=list, description="分支列表")
    warehouse_id: Optional[str] = Field(None, description="仓库ID")
    like_count: int = Field(0, description="点赞数")
    status: Optional[str] = Field(None, description="状态")
    comment_count: int = Field(0, description="评论数")


class UpdateCatalogRequest(BaseModel):
    """更新目录请求"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    prompt: str = Field("", description="提示词")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("目录名称不能为空")
        return v.strip()


class UpdateDocumentContentRequest(BaseModel):
    """更新文档内容请求"""
    id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("文档内容不能为空")
        return v.strip()


class DocumentFileItemResponse(BaseModel):
    """文档文件项响应"""
    id: str = Field(..., description="文件项ID")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="描述")
    content: Optional[str] = Field(None, description="文档实际内容")
    comment_count: int = Field(0, description="评论数量")
    size: int = Field(0, description="文档大小")
    request_token: int = Field(0, description="请求token消耗")
    response_token: int = Field(0, description="响应token")
    is_embedded: bool = Field(False, description="是否嵌入完成")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="源数据")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")
    sources: List['DocumentFileItemSourceResponse'] = Field(default_factory=list, description="相关源文件")


class DocumentFileItemSourceResponse(BaseModel):
    """文档文件项源响应"""
    id: str = Field(..., description="源ID")
    file_path: str = Field(..., description="文件路径")
    line_start: Optional[int] = Field(None, description="开始行号")
    line_end: Optional[int] = Field(None, description="结束行号")
    content: Optional[str] = Field(None, description="源内容")


# 解决循环引用
DocumentCatalogTreeItem.model_rebuild()
DocumentFileItemResponse.model_rebuild() 