from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    items: List[T] = Field(..., description="数据列表")


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")


class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间") 