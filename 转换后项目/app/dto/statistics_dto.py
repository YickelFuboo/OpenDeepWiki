from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StatisticsDto(BaseModel):
    """统计DTO"""
    id: str = Field(..., description="统计ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    type: str = Field(..., description="统计类型")
    data: str = Field(..., description="统计数据")
    date: str = Field(..., description="日期")
    hour: Optional[int] = Field(None, description="小时")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class PageViewStatisticsDto(BaseModel):
    """页面访问统计DTO"""
    date: str = Field(..., description="日期")
    page_views: int = Field(..., description="页面访问量")
    unique_visitors: int = Field(..., description="独立访客数")
    total_time: int = Field(..., description="总访问时间（秒）")


class ApiCallStatisticsDto(BaseModel):
    """API调用统计DTO"""
    date: str = Field(..., description="日期")
    total_calls: int = Field(..., description="总调用次数")
    success_calls: int = Field(..., description="成功调用次数")
    error_calls: int = Field(..., description="错误调用次数")
    avg_response_time: float = Field(..., description="平均响应时间（毫秒）")


class UserActivityStatisticsDto(BaseModel):
    """用户活动统计DTO"""
    date: str = Field(..., description="日期")
    active_users: int = Field(..., description="活跃用户数")
    new_users: int = Field(..., description="新用户数")
    total_users: int = Field(..., description="总用户数") 