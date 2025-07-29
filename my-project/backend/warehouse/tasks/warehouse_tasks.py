import logging
from celery import Celery
from sqlalchemy.orm import Session

from database import get_db
from warehouse.services.warehouse_processor import WarehouseProcessor
from models.warehouse import Warehouse, WarehouseStatus

logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery(
    "warehouse_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(bind=True)
def process_warehouse_task(self, warehouse_id: str):
    """处理仓库的后台任务"""
    try:
        logger.info(f"开始处理仓库任务: {warehouse_id}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建仓库处理器
        processor = WarehouseProcessor(db)
        
        # 处理仓库
        result = processor.process_warehouse(warehouse_id)
        
        if result["success"]:
            logger.info(f"仓库处理成功: {warehouse_id}")
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "仓库处理完成"
            }
        else:
            logger.error(f"仓库处理失败: {warehouse_id}, 错误: {result['error']}")
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": result["error"]
            }
            
    except Exception as e:
        logger.error(f"仓库处理任务异常: {warehouse_id}, 错误: {e}")
        
        # 更新仓库状态为失败
        try:
            db = next(get_db())
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if warehouse:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"更新仓库状态失败: {db_error}")
        
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        }

@celery_app.task(bind=True)
def reset_warehouse_task(self, warehouse_id: str):
    """重置仓库的后台任务"""
    try:
        logger.info(f"开始重置仓库任务: {warehouse_id}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 更新仓库状态为待处理
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "仓库不存在"
            }
        
        warehouse.status = WarehouseStatus.PENDING
        db.commit()
        
        # 重新处理仓库
        processor = WarehouseProcessor(db)
        result = processor.process_warehouse(warehouse_id)
        
        if result["success"]:
            logger.info(f"仓库重置成功: {warehouse_id}")
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "仓库重置完成"
            }
        else:
            logger.error(f"仓库重置失败: {warehouse_id}, 错误: {result['error']}")
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": result["error"]
            }
            
    except Exception as e:
        logger.error(f"仓库重置任务异常: {warehouse_id}, 错误: {e}")
        
        # 更新仓库状态为失败
        try:
            db = next(get_db())
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if warehouse:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"更新仓库状态失败: {db_error}")
        
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        }

@celery_app.task(bind=True)
def cleanup_failed_warehouses_task(self):
    """清理失败的仓库任务"""
    try:
        logger.info("开始清理失败的仓库")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找失败的仓库
        failed_warehouses = db.query(Warehouse).filter(
            Warehouse.status == WarehouseStatus.FAILED
        ).all()
        
        cleaned_count = 0
        for warehouse in failed_warehouses:
            try:
                # 清理本地文件
                import os
                import shutil
                
                local_path = os.path.join(
                    "git_repositories",  # 这里需要根据实际配置调整
                    warehouse.organization_name,
                    warehouse.name
                )
                
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    logger.info(f"清理仓库文件: {warehouse.name}")
                
                # 删除仓库记录
                db.delete(warehouse)
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"清理仓库失败: {warehouse.name}, 错误: {e}")
        
        db.commit()
        
        logger.info(f"清理失败的仓库完成，共清理 {cleaned_count} 个仓库")
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个失败的仓库"
        }
        
    except Exception as e:
        logger.error(f"清理失败仓库任务异常: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# 定时任务
@celery_app.task
def schedule_warehouse_processing():
    """定时处理待处理的仓库"""
    try:
        logger.info("开始定时处理待处理的仓库")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找待处理的仓库
        pending_warehouses = db.query(Warehouse).filter(
            Warehouse.status == WarehouseStatus.PENDING
        ).limit(5).all()  # 限制每次处理5个仓库
        
        processed_count = 0
        for warehouse in pending_warehouses:
            try:
                # 提交处理任务
                process_warehouse_task.delay(warehouse.id)
                processed_count += 1
                logger.info(f"提交仓库处理任务: {warehouse.name}")
                
            except Exception as e:
                logger.error(f"提交仓库处理任务失败: {warehouse.name}, 错误: {e}")
        
        logger.info(f"定时处理任务完成，提交了 {processed_count} 个仓库处理任务")
        
        return {
            "success": True,
            "processed_count": processed_count,
            "message": f"提交了 {processed_count} 个仓库处理任务"
        }
        
    except Exception as e:
        logger.error(f"定时处理仓库任务异常: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# 配置定时任务
celery_app.conf.beat_schedule = {
    'process-pending-warehouses': {
        'task': 'warehouse.tasks.warehouse_tasks.schedule_warehouse_processing',
        'schedule': 300.0,  # 每5分钟执行一次
    },
    'cleanup-failed-warehouses': {
        'task': 'warehouse.tasks.warehouse_tasks.cleanup_failed_warehouses_task',
        'schedule': 3600.0,  # 每小时执行一次
    },
} 