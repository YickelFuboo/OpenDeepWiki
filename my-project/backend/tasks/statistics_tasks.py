import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import get_db
from models.statistics import Statistics, AccessRecord
from models.warehouse import Warehouse
from models.document import Document
from models.user import User
from services.statistics_service import StatisticsService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def generate_statistics_task(date_str: Optional[str] = None) -> Dict[str, Any]:
    """生成统计数据的后台任务"""
    try:
        logger.info("开始生成统计数据")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 确定统计日期
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            # 默认生成昨天的统计数据
            target_date = datetime.utcnow().date() - timedelta(days=1)
        
        # 创建统计服务
        statistics_service = StatisticsService(db)
        
        # 生成统计数据
        success = statistics_service.generate_daily_statistics(target_date)
        
        if success:
            logger.info(f"统计数据生成成功，日期: {target_date}")
            return {
                "success": True,
                "date": target_date.strftime("%Y-%m-%d"),
                "message": "统计数据生成成功"
            }
        else:
            logger.warning(f"统计数据生成失败，日期: {target_date}")
            return {
                "success": False,
                "date": target_date.strftime("%Y-%m-%d"),
                "message": "统计数据生成失败"
            }
            
    except Exception as e:
        logger.error(f"生成统计数据任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def cleanup_old_access_records_task(days_to_keep: int = 90) -> Dict[str, Any]:
    """清理旧的访问记录任务"""
    try:
        logger.info(f"开始清理旧的访问记录，保留天数: {days_to_keep}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 计算截止日期
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除旧的访问记录
        deleted_count = db.query(AccessRecord).filter(
            AccessRecord.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"访问记录清理完成，删除了 {deleted_count} 条记录")
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
            "message": f"清理了 {deleted_count} 条旧的访问记录"
        }
        
    except Exception as e:
        logger.error(f"清理访问记录任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def generate_system_statistics_task() -> Dict[str, Any]:
    """生成系统统计信息任务"""
    try:
        logger.info("开始生成系统统计信息")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 统计用户数量
        user_count = db.query(User).filter(User.is_active == True).count()
        
        # 统计仓库数量
        warehouse_count = db.query(Warehouse).filter(
            Warehouse.is_deleted == False
        ).count()
        
        # 统计文档数量
        document_count = db.query(Document).count()
        
        # 统计今日访问量
        today = datetime.utcnow().date()
        today_access_count = db.query(AccessRecord).filter(
            func.date(AccessRecord.created_at) == today
        ).count()
        
        # 统计本周访问量
        week_start = today - timedelta(days=today.weekday())
        week_access_count = db.query(AccessRecord).filter(
            AccessRecord.created_at >= week_start
        ).count()
        
        # 统计本月访问量
        month_start = today.replace(day=1)
        month_access_count = db.query(AccessRecord).filter(
            AccessRecord.created_at >= month_start
        ).count()
        
        # 保存统计信息
        statistics = Statistics(
            id=f"system_{datetime.utcnow().strftime('%Y%m%d')}",
            type="system",
            data={
                "user_count": user_count,
                "warehouse_count": warehouse_count,
                "document_count": document_count,
                "today_access_count": today_access_count,
                "week_access_count": week_access_count,
                "month_access_count": month_access_count,
                "generated_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(statistics)
        db.commit()
        
        logger.info("系统统计信息生成成功")
        return {
            "success": True,
            "statistics": {
                "user_count": user_count,
                "warehouse_count": warehouse_count,
                "document_count": document_count,
                "today_access_count": today_access_count,
                "week_access_count": week_access_count,
                "month_access_count": month_access_count
            },
            "message": "系统统计信息生成成功"
        }
        
    except Exception as e:
        logger.error(f"生成系统统计信息任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def generate_warehouse_statistics_task(warehouse_id: str) -> Dict[str, Any]:
    """生成仓库统计信息任务"""
    try:
        logger.info(f"开始生成仓库统计信息: {warehouse_id}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 获取仓库信息
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "仓库不存在"
            }
        
        # 统计仓库相关数据
        document_count = db.query(Document).filter(
            Document.warehouse_id == warehouse_id
        ).count()
        
        # 统计访问记录
        access_count = db.query(AccessRecord).filter(
            AccessRecord.resource_type == "warehouse",
            AccessRecord.resource_id == warehouse_id
        ).count()
        
        # 统计今日访问
        today = datetime.utcnow().date()
        today_access_count = db.query(AccessRecord).filter(
            and_(
                AccessRecord.resource_type == "warehouse",
                AccessRecord.resource_id == warehouse_id,
                func.date(AccessRecord.created_at) == today
            )
        ).count()
        
        # 保存统计信息
        statistics = Statistics(
            id=f"warehouse_{warehouse_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            type="warehouse",
            resource_id=warehouse_id,
            data={
                "document_count": document_count,
                "access_count": access_count,
                "today_access_count": today_access_count,
                "warehouse_name": warehouse.name,
                "warehouse_status": warehouse.status.value,
                "generated_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(statistics)
        db.commit()
        
        logger.info(f"仓库统计信息生成成功: {warehouse_id}")
        return {
            "success": True,
            "warehouse_id": warehouse_id,
            "statistics": {
                "document_count": document_count,
                "access_count": access_count,
                "today_access_count": today_access_count
            },
            "message": "仓库统计信息生成成功"
        }
        
    except Exception as e:
        logger.error(f"生成仓库统计信息任务异常: {warehouse_id}, 错误: {str(e)}")
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        } 