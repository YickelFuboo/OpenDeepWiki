from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.simple_auth import get_current_active_user, require_admin
from app.dto.statistics_dto import StatisticsDto
from app.services.statistics_service import StatisticsService
from app.core.simple_auth import SimpleUserContext

statistics_router = APIRouter()


@statistics_router.get("/page-views")
@require_admin()
async def get_page_view_statistics(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取页面访问统计（管理员）"""
    statistics_service = StatisticsService(db)
    
    try:
        stats = await statistics_service.get_page_view_statistics(start_date, end_date)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@statistics_router.get("/api-calls")
@require_admin()
async def get_api_call_statistics(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API调用统计（管理员）"""
    statistics_service = StatisticsService(db)
    
    try:
        stats = await statistics_service.get_api_call_statistics(start_date, end_date)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@statistics_router.get("/user-activity")
@require_admin()
async def get_user_activity_statistics(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户活动统计（管理员）"""
    statistics_service = StatisticsService(db)
    
    try:
        stats = await statistics_service.get_user_activity_statistics(start_date, end_date)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 