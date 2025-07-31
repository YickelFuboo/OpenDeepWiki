from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from schemas.common import TimestampMixin

class DocumentStatus(str, Enum):
    """文档状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    """文档类型枚举"""
    FILE = "file"
    DIRECTORY = "directory"

class DocumentBase(BaseModel):
    """文档基础模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    title: str = Field(..., description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    git_path: Optional[str] = Field(None, description="Git路径")

class DocumentCreate(DocumentBase):
    """创建文档请求模型"""
    pass

class DocumentUpdate(BaseModel):
    """更新文档请求模型"""
    title: Optional[str] = Field(None, description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    status: Optional[DocumentStatus] = Field(None, description="文档状态")

class DocumentResponse(DocumentBase, TimestampMixin):
    """文档响应模型"""
    id: str = Field(..., description="文档ID")
    status: DocumentStatus = Field(..., description="文档状态")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")
    like_count: int = Field(0, description="点赞数")
    comment_count: int = Field(0, description="评论数")

    class Config:
        from_attributes = True

class DocumentCatalogBase(BaseModel):
    """文档目录基础模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    parent_id: Optional[str] = Field(None, description="父目录ID")
    title: str = Field(..., description="目录标题")
    name: str = Field(..., description="目录名称")
    type: DocumentType = Field(DocumentType.DIRECTORY, description="目录类型")
    prompt: Optional[str] = Field(None, description="提示词")
    order_index: Optional[int] = Field(0, description="排序索引")

class DocumentCatalogCreate(DocumentCatalogBase):
    """创建文档目录请求模型"""
    pass

class DocumentCatalogUpdate(BaseModel):
    """更新文档目录请求模型"""
    title: Optional[str] = Field(None, description="目录标题")
    name: Optional[str] = Field(None, description="目录名称")
    prompt: Optional[str] = Field(None, description="提示词")
    order_index: Optional[int] = Field(None, description="排序索引")

class DocumentCatalogResponse(DocumentCatalogBase, TimestampMixin):
    """文档目录响应模型"""
    id: str = Field(..., description="目录ID")
    content: Optional[str] = Field(None, description="目录内容")
    is_completed: bool = Field(False, description="是否完成")
    is_deleted: bool = Field(False, description="是否删除")
    children: Optional[List['DocumentCatalogResponse']] = Field(None, description="子目录")

    class Config:
        from_attributes = True

class DocumentFileItemBase(BaseModel):
    """文档文件项基础模型"""
    document_catalog_id: str = Field(..., description="文档目录ID")
    title: str = Field(..., description="文件标题")
    content: str = Field(..., description="文件内容")

class DocumentFileItemCreate(DocumentFileItemBase):
    """创建文档文件项请求模型"""
    pass

class DocumentFileItemUpdate(BaseModel):
    """更新文档文件项请求模型"""
    title: Optional[str] = Field(None, description="文件标题")
    content: Optional[str] = Field(None, description="文件内容")

class DocumentFileItemResponse(DocumentFileItemBase, TimestampMixin):
    """文档文件项响应模型"""
    id: str = Field(..., description="文件项ID")

    class Config:
        from_attributes = True

class DocumentFileItemSourceBase(BaseModel):
    """文档文件源基础模型"""
    document_file_item_id: str = Field(..., description="文档文件项ID")
    name: str = Field(..., description="源文件名称")
    address: str = Field(..., description="源文件地址")

class DocumentFileItemSourceCreate(DocumentFileItemSourceBase):
    """创建文档文件源请求模型"""
    pass

class DocumentFileItemSourceResponse(DocumentFileItemSourceBase, TimestampMixin):
    """文档文件源响应模型"""
    id: str = Field(..., description="源文件ID")

    class Config:
        from_attributes = True

class DocumentContentResponse(BaseModel):
    """文档内容响应模型"""
    content: str = Field(..., description="文档内容")
    title: str = Field(..., description="文档标题")
    file_sources: List[DocumentFileItemSourceResponse] = Field(..., description="文件源列表")
    address: str = Field(..., description="仓库地址")
    branch: Optional[str] = Field(None, description="分支名称")
    last_update: datetime = Field(..., description="最后更新时间")
    document_catalog_id: str = Field(..., description="文档目录ID")

class DocumentCatalogTreeResponse(BaseModel):
    """文档目录树响应模型"""
    items: List[DocumentCatalogResponse] = Field(..., description="目录项列表")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")
    description: Optional[str] = Field(None, description="描述")
    progress: int = Field(0, description="进度百分比")
    git: str = Field(..., description="Git地址")
    branches: List[str] = Field(..., description="分支列表")
    warehouse_id: str = Field(..., description="仓库ID")
    like_count: int = Field(0, description="点赞数")
    status: str = Field(..., description="状态")
    comment_count: int = Field(0, description="评论数")

class UpdateCatalogRequest(BaseModel):
    """更新目录请求模型"""
    id: str = Field(..., description="目录ID")
    name: str = Field(..., description="目录名称")
    prompt: str = Field(..., description="提示词")

class UpdateDocumentContentRequest(BaseModel):
    """更新文档内容请求模型"""
    id: str = Field(..., description="文档目录ID")
    content: str = Field(..., description="文档内容")

# 解决循环引用
DocumentCatalogResponse.model_rebuild() 