import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_

from app.db.connection import get_db
from models.warehouse import Warehouse, WarehouseStatus
from models.document import Document
from models.minimap import MiniMap
from ai.services.minimap_service import MiniMapService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def generate_minimap_task() -> Dict[str, Any]:
    """生成思维导图的后台任务"""
    try:
        logger.info("开始生成思维导图任务")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 获取已存在的思维导图ID列表
        existing_minimap_ids = db.query(MiniMap.warehouse_id).all()
        existing_minimap_ids = [item[0] for item in existing_minimap_ids]
        
        # 查询需要生成思维导图的仓库
        warehouses = db.query(Warehouse).filter(
            and_(
                Warehouse.status == WarehouseStatus.COMPLETED,
                not_(Warehouse.id.in_(existing_minimap_ids))
            )
        ).order_by(Warehouse.created_at).limit(3).all()  # 每次最多处理3个仓库
        
        if not warehouses:
            logger.info("没有需要生成思维导图的仓库")
            return {
                "success": True,
                "processed_count": 0,
                "message": "没有需要生成思维导图的仓库"
            }
        
        logger.info(f"找到 {len(warehouses)} 个仓库需要生成思维导图")
        
        processed_count = 0
        error_count = 0
        
        for warehouse in warehouses:
            try:
                logger.info(f"开始处理仓库 {warehouse.name} 的思维导图")
                
                # 获取文档信息
                document = db.query(Document).filter(
                    Document.warehouse_id == warehouse.id
                ).first()
                
                if not document:
                    logger.warning(f"仓库 {warehouse.name} 没有对应的文档")
                    continue
                
                # 创建思维导图服务
                minimap_service = MiniMapService()
                
                # 生成思维导图
                minimap_data = await minimap_service.generate_minimap(
                    warehouse.optimized_directory_structure,
                    warehouse,
                    document.git_path
                )
                
                if minimap_data:
                    # 保存思维导图
                    minimap = MiniMap(
                        id=f"minimap_{warehouse.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        warehouse_id=warehouse.id,
                        value=json.dumps(minimap_data, ensure_ascii=False),
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(minimap)
                    db.commit()
                    
                    logger.info(f"仓库 {warehouse.name} 的思维导图生成成功")
                    processed_count += 1
                else:
                    logger.warning(f"仓库 {warehouse.name} 的思维导图生成失败")
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"处理仓库 {warehouse.name} 思维导图时发生异常: {str(e)}")
                error_count += 1
        
        logger.info(f"思维导图生成任务完成，成功 {processed_count} 个，失败 {error_count} 个")
        return {
            "success": True,
            "processed_count": processed_count,
            "error_count": error_count,
            "message": f"思维导图生成完成，成功 {processed_count} 个，失败 {error_count} 个"
        }
        
    except Exception as e:
        logger.error(f"思维导图生成任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def regenerate_minimap_task(warehouse_id: str) -> Dict[str, Any]:
    """重新生成指定仓库的思维导图"""
    try:
        logger.info(f"开始重新生成仓库 {warehouse_id} 的思维导图")
        
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
        
        # 删除旧的思维导图
        db.query(MiniMap).filter(MiniMap.warehouse_id == warehouse_id).delete()
        
        # 创建思维导图服务
        minimap_service = MiniMapService()
        
        # 生成新的思维导图
        minimap_data = await minimap_service.generate_minimap(
            warehouse.optimized_directory_structure,
            warehouse,
            document.git_path
        )
        
        if minimap_data:
            # 保存新的思维导图
            minimap = MiniMap(
                id=f"minimap_{warehouse_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                warehouse_id=warehouse_id,
                value=json.dumps(minimap_data, ensure_ascii=False),
                created_at=datetime.utcnow()
            )
            
            db.add(minimap)
            db.commit()
            
            logger.info(f"仓库 {warehouse.name} 的思维导图重新生成成功")
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "思维导图重新生成成功"
            }
        else:
            logger.error(f"仓库 {warehouse.name} 的思维导图重新生成失败")
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "思维导图生成失败"
            }
            
    except Exception as e:
        logger.error(f"重新生成思维导图任务异常: {warehouse_id}, 错误: {str(e)}")
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        }

def cleanup_old_minimaps_task(days_to_keep: int = 90) -> Dict[str, Any]:
    """清理旧的思维导图任务"""
    try:
        logger.info(f"开始清理旧的思维导图，保留天数: {days_to_keep}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 计算截止日期
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 删除旧的思维导图
        deleted_count = db.query(MiniMap).filter(
            MiniMap.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"思维导图清理完成，删除了 {deleted_count} 条记录")
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
            "message": f"清理了 {deleted_count} 条旧的思维导图"
        }
        
    except Exception as e:
        logger.error(f"清理思维导图任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def validate_minimap_task(warehouse_id: str) -> Dict[str, Any]:
    """验证思维导图数据完整性任务"""
    try:
        logger.info(f"开始验证仓库 {warehouse_id} 的思维导图")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 获取思维导图
        minimap = db.query(MiniMap).filter(
            MiniMap.warehouse_id == warehouse_id
        ).first()
        
        if not minimap:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": "思维导图不存在"
            }
        
        # 验证JSON数据
        try:
            minimap_data = json.loads(minimap.value)
            
            # 检查必要字段
            required_fields = ["nodes", "edges", "metadata"]
            missing_fields = [field for field in required_fields if field not in minimap_data]
            
            if missing_fields:
                return {
                    "success": False,
                    "warehouse_id": warehouse_id,
                    "error": f"思维导图数据缺少必要字段: {missing_fields}"
                }
            
            # 检查节点和边的数量
            node_count = len(minimap_data.get("nodes", []))
            edge_count = len(minimap_data.get("edges", []))
            
            logger.info(f"仓库 {warehouse_id} 的思维导图验证成功，节点数: {node_count}, 边数: {edge_count}")
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "node_count": node_count,
                "edge_count": edge_count,
                "message": "思维导图数据验证成功"
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "warehouse_id": warehouse_id,
                "error": f"思维导图JSON数据格式错误: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"验证思维导图任务异常: {warehouse_id}, 错误: {str(e)}")
        return {
            "success": False,
            "warehouse_id": warehouse_id,
            "error": str(e)
        } 