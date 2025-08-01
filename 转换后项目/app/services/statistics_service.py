import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from src.models.statistics import Statistics
from src.dto.statistics_dto import (
    PageViewStatisticsDto, 
    ApiCallStatisticsDto, 
    UserActivityStatisticsDto
)


class StatisticsService:
    """统计服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_statistics(
        self, 
        stat_type: str, 
        data: Dict[str, Any], 
        user_id: str = None,
        date: str = None,
        hour: int = None
    ) -> None:
        """记录统计数据"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stat = Statistics(
            id=f"{stat_type}_{date}_{hour or 0}_{user_id or 'anonymous'}",
            user_id=user_id,
            type=stat_type,
            data=json.dumps(data),
            date=date,
            hour=hour,
            created_at=datetime.utcnow()
        )
        
        self.db.add(stat)
        await self.db.commit()
        
        logger.info(f"Recorded statistics: {stat_type} for date {date}")
    
    async def get_page_view_statistics(self, start_date: str, end_date: str) -> List[PageViewStatisticsDto]:
        """获取页面访问统计"""
        # 验证日期格式
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 查询统计数据
        result = await self.db.execute(
            select(Statistics)
            .where(
                Statistics.type == "page_view",
                Statistics.date >= start_date,
                Statistics.date <= end_date
            )
            .order_by(Statistics.date)
        )
        
        stats = result.scalars().all()
        
        # 处理统计数据
        page_view_stats = []
        for stat in stats:
            try:
                data = json.loads(stat.data)
                page_view_stats.append(PageViewStatisticsDto(
                    date=stat.date,
                    page_views=data.get("page_views", 0),
                    unique_visitors=data.get("unique_visitors", 0),
                    total_time=data.get("total_time", 0)
                ))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data in statistics: {stat.id}")
                continue
        
        return page_view_stats
    
    async def get_api_call_statistics(self, start_date: str, end_date: str) -> List[ApiCallStatisticsDto]:
        """获取API调用统计"""
        # 验证日期格式
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 查询统计数据
        result = await self.db.execute(
            select(Statistics)
            .where(
                Statistics.type == "api_call",
                Statistics.date >= start_date,
                Statistics.date <= end_date
            )
            .order_by(Statistics.date)
        )
        
        stats = result.scalars().all()
        
        # 处理统计数据
        api_call_stats = []
        for stat in stats:
            try:
                data = json.loads(stat.data)
                api_call_stats.append(ApiCallStatisticsDto(
                    date=stat.date,
                    total_calls=data.get("total_calls", 0),
                    success_calls=data.get("success_calls", 0),
                    error_calls=data.get("error_calls", 0),
                    avg_response_time=data.get("avg_response_time", 0.0)
                ))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data in statistics: {stat.id}")
                continue
        
        return api_call_stats
    
    async def get_user_activity_statistics(self, start_date: str, end_date: str) -> List[UserActivityStatisticsDto]:
        """获取用户活动统计"""
        # 验证日期格式
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 查询统计数据
        result = await self.db.execute(
            select(Statistics)
            .where(
                Statistics.type == "user_activity",
                Statistics.date >= start_date,
                Statistics.date <= end_date
            )
            .order_by(Statistics.date)
        )
        
        stats = result.scalars().all()
        
        # 处理统计数据
        user_activity_stats = []
        for stat in stats:
            try:
                data = json.loads(stat.data)
                user_activity_stats.append(UserActivityStatisticsDto(
                    date=stat.date,
                    active_users=data.get("active_users", 0),
                    new_users=data.get("new_users", 0),
                    total_users=data.get("total_users", 0)
                ))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON data in statistics: {stat.id}")
                continue
        
        return user_activity_stats 