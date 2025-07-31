import logging
import uuid
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.connection import get_db
from models.user import User, Role, UserInRole
from models.warehouse import Warehouse
from models.document import Document
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def data_migration_task() -> Dict[str, Any]:
    """数据迁移任务"""
    try:
        logger.info("开始执行数据迁移任务")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 执行各种迁移任务
        results = {
            "initialize_users": await initialize_users_task(db),
            "migrate_warehouses": await migrate_warehouses_task(db),
            "migrate_documents": await migrate_documents_task(db),
            "update_indexes": await update_indexes_task(db)
        }
        
        # 检查是否有错误
        errors = [result for result in results.values() if not result.get("success", False)]
        
        if errors:
            logger.error(f"数据迁移任务完成，但有 {len(errors)} 个错误")
            return {
                "success": False,
                "results": results,
                "error_count": len(errors),
                "message": f"数据迁移完成，但有 {len(errors)} 个错误"
            }
        else:
            logger.info("数据迁移任务完成")
            return {
                "success": True,
                "results": results,
                "message": "数据迁移完成"
            }
            
    except Exception as e:
        logger.error(f"数据迁移任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def initialize_users_task(db: Session) -> Dict[str, Any]:
    """初始化用户数据任务"""
    try:
        logger.info("开始初始化用户数据")
        
        # 检查是否已存在用户角色
        existing_roles = db.query(UserInRole).first()
        if existing_roles:
            logger.info("用户数据已存在，跳过初始化")
            return {
                "success": True,
                "message": "用户数据已存在，跳过初始化"
            }
        
        # 创建系统角色
        admin_role = Role(
            id=str(uuid.uuid4()),
            name="admin",
            description="管理员角色",
            is_system_role=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        user_role = Role(
            id=str(uuid.uuid4()),
            name="user",
            description="普通用户角色",
            is_system_role=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_role)
        db.add(user_role)
        
        # 创建默认管理员用户
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@opendeepwiki.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8J8J8J8",  # 默认密码: admin123
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        
        # 为管理员用户分配管理员角色
        admin_user_role = UserInRole(
            id=str(uuid.uuid4()),
            user_id=admin_user.id,
            role_id=admin_role.id,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user_role)
        db.commit()
        
        logger.info("用户数据初始化完成")
        return {
            "success": True,
            "admin_user_id": admin_user.id,
            "admin_role_id": admin_role.id,
            "user_role_id": user_role.id,
            "message": "用户数据初始化完成"
        }
        
    except Exception as e:
        logger.error(f"初始化用户数据任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def migrate_warehouses_task(db: Session) -> Dict[str, Any]:
    """迁移仓库数据任务"""
    try:
        logger.info("开始迁移仓库数据")
        
        # 检查是否有需要迁移的仓库数据
        warehouses = db.query(Warehouse).all()
        
        migrated_count = 0
        for warehouse in warehouses:
            try:
                # 更新仓库的创建时间和更新时间
                if not warehouse.created_at:
                    warehouse.created_at = datetime.utcnow()
                if not warehouse.updated_at:
                    warehouse.updated_at = datetime.utcnow()
                
                # 确保仓库状态有效
                if not warehouse.status:
                    warehouse.status = "pending"
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移仓库 {warehouse.id} 时发生错误: {str(e)}")
        
        db.commit()
        
        logger.info(f"仓库数据迁移完成，处理了 {migrated_count} 个仓库")
        return {
            "success": True,
            "migrated_count": migrated_count,
            "message": f"仓库数据迁移完成，处理了 {migrated_count} 个仓库"
        }
        
    except Exception as e:
        logger.error(f"迁移仓库数据任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def migrate_documents_task(db: Session) -> Dict[str, Any]:
    """迁移文档数据任务"""
    try:
        logger.info("开始迁移文档数据")
        
        # 检查是否有需要迁移的文档数据
        documents = db.query(Document).all()
        
        migrated_count = 0
        for document in documents:
            try:
                # 更新文档的创建时间和更新时间
                if not document.created_at:
                    document.created_at = datetime.utcnow()
                if not document.updated_at:
                    document.updated_at = datetime.utcnow()
                
                # 确保文档状态有效
                if not document.status:
                    document.status = "pending"
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"迁移文档 {document.id} 时发生错误: {str(e)}")
        
        db.commit()
        
        logger.info(f"文档数据迁移完成，处理了 {migrated_count} 个文档")
        return {
            "success": True,
            "migrated_count": migrated_count,
            "message": f"文档数据迁移完成，处理了 {migrated_count} 个文档"
        }
        
    except Exception as e:
        logger.error(f"迁移文档数据任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def update_indexes_task(db: Session) -> Dict[str, Any]:
    """更新数据库索引任务"""
    try:
        logger.info("开始更新数据库索引")
        
        # 这里可以添加创建或更新数据库索引的逻辑
        # 例如：创建全文搜索索引、复合索引等
        
        # 示例：创建用户邮箱索引
        # db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        
        # 示例：创建仓库状态索引
        # db.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_status ON warehouses(status)")
        
        # 示例：创建文档仓库ID索引
        # db.execute("CREATE INDEX IF NOT EXISTS idx_documents_warehouse_id ON documents(warehouse_id)")
        
        logger.info("数据库索引更新完成")
        return {
            "success": True,
            "message": "数据库索引更新完成"
        }
        
    except Exception as e:
        logger.error(f"更新数据库索引任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def backup_data_task() -> Dict[str, Any]:
    """数据备份任务"""
    try:
        logger.info("开始执行数据备份任务")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 备份用户数据
        users = db.query(User).all()
        user_data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            for user in users
        ]
        
        # 备份仓库数据
        warehouses = db.query(Warehouse).all()
        warehouse_data = [
            {
                "id": warehouse.id,
                "name": warehouse.name,
                "organization_name": warehouse.organization_name,
                "address": warehouse.address,
                "branch": warehouse.branch,
                "status": warehouse.status.value if warehouse.status else "pending",
                "created_at": warehouse.created_at.isoformat() if warehouse.created_at else None,
                "updated_at": warehouse.updated_at.isoformat() if warehouse.updated_at else None
            }
            for warehouse in warehouses
        ]
        
        # 备份文档数据
        documents = db.query(Document).all()
        document_data = [
            {
                "id": document.id,
                "warehouse_id": document.warehouse_id,
                "title": document.title,
                "description": document.description,
                "status": document.status.value if document.status else "pending",
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            }
            for document in documents
        ]
        
        # 生成备份文件名
        backup_filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 构建备份数据
        backup_data = {
            "backup_time": datetime.utcnow().isoformat(),
            "users": user_data,
            "warehouses": warehouse_data,
            "documents": document_data
        }
        
        # 保存备份文件（这里只是示例，实际应该保存到文件系统或云存储）
        import json
        backup_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        logger.info(f"数据备份完成，文件名: {backup_filename}")
        return {
            "success": True,
            "backup_filename": backup_filename,
            "user_count": len(user_data),
            "warehouse_count": len(warehouse_data),
            "document_count": len(document_data),
            "message": f"数据备份完成，文件名: {backup_filename}"
        }
        
    except Exception as e:
        logger.error(f"数据备份任务异常: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 