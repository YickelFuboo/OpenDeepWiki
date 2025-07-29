import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.access_log import AccessLog
from models.statistics import AccessRecord
from services.statistics_service import StatisticsService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 访问日志队列（内存队列，生产环境建议使用Redis）
class AccessLogQueue:
    def __init__(self):
        self.queue = []
        self.max_size = 1000
    
    def enqueue(self, log_entry: Dict[str, Any]):
        """添加日志条目到队列"""
        if len(self.queue) < self.max_size:
            self.queue.append(log_entry)
        else:
            logger.warning("访问日志队列已满，丢弃新条目")
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """从队列中取出日志条目"""
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def size(self) -> int:
        """获取队列大小"""
        return len(self.queue)

# 全局访问日志队列实例
access_log_queue = AccessLogQueue()

def enqueue_access_log(log_data: Dict[str, Any]) -> bool:
    """将访问日志添加到队列"""
    try:
        access_log_queue.enqueue(log_data)
        return True
    except Exception as e:
        logger.error(f"添加访问日志到队列失败: {str(e)}")
        return False

def process_access_log_task() -> Dict[str, Any]:
    """处理访问日志的后台任务"""
    try:
        logger.info("开始处理访问日志")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建统计服务
        statistics_service = StatisticsService(db)
        
        processed_count = 0
        error_count = 0
        
        # 处理队列中的日志条目
        while access_log_queue.size() > 0:
            try:
                log_entry = access_log_queue.dequeue()
                if log_entry:
                    # 处理日志条目
                    await process_log_entry(statistics_service, log_entry)
                    processed_count += 1
                    
                    # 每处理100条记录提交一次
                    if processed_count % 100 == 0:
                        db.commit()
                        
            except Exception as e:
                logger.error(f"处理访问日志条目失败: {str(e)}")
                error_count += 1
        
        # 最终提交
        db.commit()
        
        logger.info(f"访问日志处理完成，处理了 {processed_count} 条记录，错误 {error_count} 条")
        return {
            "success": True,
            "processed_count": processed_count,
            "error_count": error_count,
            "message": f"处理了 {processed_count} 条访问日志"
        }
        
    except Exception as e:
        logger.error(f"访问日志处理任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def process_log_entry(statistics_service: StatisticsService, log_entry: Dict[str, Any]):
    """处理单个日志条目"""
    try:
        # 记录访问统计
        await statistics_service.record_access(
            resource_type=log_entry.get("resource_type", "unknown"),
            resource_id=log_entry.get("resource_id", ""),
            user_id=log_entry.get("user_id"),
            ip_address=log_entry.get("ip_address", ""),
            user_agent=log_entry.get("user_agent", ""),
            path=log_entry.get("path", ""),
            method=log_entry.get("method", ""),
            status_code=log_entry.get("status_code", 0),
            response_time=log_entry.get("response_time", 0)
        )
        
    except Exception as e:
        logger.error(f"处理日志条目失败: {log_entry}, 错误: {str(e)}")
        raise

def cleanup_old_access_logs_task(days_to_keep: int = 30) -> Dict[str, Any]:
    """清理旧的访问日志任务"""
    try:
        logger.info(f"开始清理旧的访问日志，保留天数: {days_to_keep}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 计算截止日期
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除旧的访问日志
        deleted_count = db.query(AccessLog).filter(
            AccessLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"访问日志清理完成，删除了 {deleted_count} 条记录")
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
            "message": f"清理了 {deleted_count} 条旧的访问日志"
        }
        
    except Exception as e:
        logger.error(f"清理访问日志任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def generate_access_statistics_task() -> Dict[str, Any]:
    """生成访问统计信息任务"""
    try:
        logger.info("开始生成访问统计信息")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 统计今日访问
        today = datetime.utcnow().date()
        today_access_count = db.query(AccessRecord).filter(
            func.date(AccessRecord.created_at) == today
        ).count()
        
        # 统计本周访问
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        week_access_count = db.query(AccessRecord).filter(
            AccessRecord.created_at >= week_start
        ).count()
        
        # 统计本月访问
        month_start = today.replace(day=1)
        month_access_count = db.query(AccessRecord).filter(
            AccessRecord.created_at >= month_start
        ).count()
        
        # 统计访问最多的资源
        top_resources = db.query(
            AccessRecord.resource_type,
            AccessRecord.resource_id,
            func.count(AccessRecord.id).label("access_count")
        ).filter(
            AccessRecord.created_at >= month_start
        ).group_by(
            AccessRecord.resource_type,
            AccessRecord.resource_id
        ).order_by(
            func.count(AccessRecord.id).desc()
        ).limit(10).all()
        
        # 保存统计信息
        from models.statistics import Statistics
        statistics = Statistics(
            id=f"access_{datetime.utcnow().strftime('%Y%m%d')}",
            type="access",
            data={
                "today_access_count": today_access_count,
                "week_access_count": week_access_count,
                "month_access_count": month_access_count,
                "top_resources": [
                    {
                        "resource_type": resource.resource_type,
                        "resource_id": resource.resource_id,
                        "access_count": resource.access_count
                    }
                    for resource in top_resources
                ],
                "generated_at": datetime.utcnow().isoformat()
            },
            created_at=datetime.utcnow()
        )
        
        db.add(statistics)
        db.commit()
        
        logger.info("访问统计信息生成成功")
        return {
            "success": True,
            "statistics": {
                "today_access_count": today_access_count,
                "week_access_count": week_access_count,
                "month_access_count": month_access_count,
                "top_resources_count": len(top_resources)
            },
            "message": "访问统计信息生成成功"
        }
        
    except Exception as e:
        logger.error(f"生成访问统计信息任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 