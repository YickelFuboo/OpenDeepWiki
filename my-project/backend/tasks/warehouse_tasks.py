import logging
import time
from typing import Optional, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from models.warehouse import Warehouse, WarehouseStatus
from models.document import Document
from warehouse.services.warehouse_processor import WarehouseProcessor
from warehouse.services.warehouse_service import WarehouseService
from utils.git_utils import GitUtils
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def process_warehouse_task(warehouse_id: str) -> Dict[str, Any]:
    """处理仓库的后台任务"""
    try:
        logger.info(f"开始处理仓库任务: {warehouse_id}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 更新任务状态
        if current_task:
            current_task.update_state(
                state="PROGRESS",
                meta={"warehouse_id": warehouse_id, "status": "开始处理"}
            )
        
        # 获取仓库信息
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "仓库不存在"
            }
        
        # 更新仓库状态为处理中
        warehouse.status = WarehouseStatus.PROCESSING
        warehouse.updated_at = time.time()
        db.commit()
        
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
        logger.error(f"仓库处理任务异常: {warehouse_id}, 错误: {str(e)}")
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        }

def schedule_warehouse_processing() -> Dict[str, Any]:
    """调度仓库处理任务 - 查找待处理的仓库并提交任务"""
    try:
        logger.info("开始调度仓库处理任务")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找待处理或处理中的仓库，优先处理正在处理中的仓库
        warehouses = db.query(Warehouse).filter(
            or_(
                Warehouse.status == WarehouseStatus.PENDING,
                Warehouse.status == WarehouseStatus.PROCESSING
            )
        ).order_by(
            Warehouse.status == WarehouseStatus.PROCESSING.desc()
        ).limit(5).all()  # 每次最多处理5个仓库
        
        processed_count = 0
        for warehouse in warehouses:
            try:
                # 提交处理任务
                from tasks.celery_app import celery_app
                task = celery_app.send_task(
                    "tasks.warehouse_tasks.process_warehouse_task",
                    args=[warehouse.id],
                    queue="warehouse"
                )
                logger.info(f"已提交仓库处理任务: {warehouse.id}, 任务ID: {task.id}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"提交仓库处理任务失败: {warehouse.id}, 错误: {str(e)}")
        
        logger.info(f"仓库处理任务调度完成，处理了 {processed_count} 个仓库")
        return {
            "success": True,
            "processed_count": processed_count,
            "message": f"调度了 {processed_count} 个仓库处理任务"
        }
        
    except Exception as e:
        logger.error(f"仓库处理任务调度异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def schedule_warehouse_updates() -> Dict[str, Any]:
    """调度仓库增量更新任务"""
    try:
        logger.info("开始调度仓库增量更新任务")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 读取环境变量，获取更新间隔
        update_interval = 7  # 默认7天
        if hasattr(settings, 'update_interval'):
            update_interval = settings.update_interval
        
        # 查找已完成且超过更新间隔的仓库
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=update_interval)
        
        warehouses = db.query(Warehouse).filter(
            and_(
                Warehouse.status == WarehouseStatus.COMPLETED,
                Warehouse.updated_at < cutoff_date
            )
        ).limit(3).all()  # 每次最多处理3个仓库
        
        updated_count = 0
        for warehouse in warehouses:
            try:
                # 检查是否有对应的文档
                document = db.query(Document).filter(
                    Document.warehouse_id == warehouse.id
                ).first()
                
                if document and document.last_update < cutoff_date:
                    # 提交增量更新任务
                    from tasks.celery_app import celery_app
                    task = celery_app.send_task(
                        "tasks.warehouse_tasks.process_warehouse_update_task",
                        args=[warehouse.id],
                        queue="warehouse"
                    )
                    logger.info(f"已提交仓库增量更新任务: {warehouse.id}, 任务ID: {task.id}")
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"提交仓库增量更新任务失败: {warehouse.id}, 错误: {str(e)}")
        
        logger.info(f"仓库增量更新任务调度完成，处理了 {updated_count} 个仓库")
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"调度了 {updated_count} 个仓库增量更新任务"
        }
        
    except Exception as e:
        logger.error(f"仓库增量更新任务调度异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def process_warehouse_update_task(warehouse_id: str) -> Dict[str, Any]:
    """处理仓库增量更新任务"""
    try:
        logger.info(f"开始处理仓库增量更新任务: {warehouse_id}")
        
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
        
        # 获取文档信息
        document = db.query(Document).filter(Document.warehouse_id == warehouse_id).first()
        if not document:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "文档不存在"
            }
        
        # 更新仓库
        git_utils = GitUtils()
        commits = git_utils.pull_repository(document.git_path, warehouse.branch)
        
        if not commits:
            logger.info(f"仓库 {warehouse_id} 没有新的提交")
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "没有新的提交"
            }
        
        # 更新文档
        document.last_update = time.time()
        db.commit()
        
        logger.info(f"仓库增量更新完成: {warehouse_id}, 获取到 {len(commits)} 个新提交")
        return {
            "success": True,
            "warehouse_id": warehouse_id,
            "message": f"增量更新完成，获取到 {len(commits)} 个新提交"
        }
        
    except Exception as e:
        logger.error(f"仓库增量更新任务异常: {warehouse_id}, 错误: {str(e)}")
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        }

def cleanup_failed_warehouses_task() -> Dict[str, Any]:
    """清理失败的仓库任务"""
    try:
        logger.info("开始清理失败的仓库")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查找失败状态超过24小时的仓库
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        failed_warehouses = db.query(Warehouse).filter(
            and_(
                Warehouse.status == WarehouseStatus.FAILED,
                Warehouse.updated_at < cutoff_time
            )
        ).all()
        
        cleaned_count = 0
        for warehouse in failed_warehouses:
            try:
                # 软删除失败的仓库
                warehouse.is_deleted = True
                warehouse.deleted_time = datetime.utcnow()
                warehouse.updated_at = datetime.utcnow()
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"清理失败仓库异常: {warehouse.id}, 错误: {str(e)}")
        
        db.commit()
        
        logger.info(f"失败仓库清理完成，清理了 {cleaned_count} 个仓库")
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个失败的仓库"
        }
        
    except Exception as e:
        logger.error(f"清理失败仓库任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 