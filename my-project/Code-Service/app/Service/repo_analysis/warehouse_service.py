import logging
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


from app.config.settings import get_settings
from app.db.models.role import UserInRole, WarehouseInRole
from app.db.models.user import User
from app.db.models.warehouse import Warehouse, WarehouseStatus, WarehouseType
from app.schemas.warehouse import (
    CreateRepositoryDto, RepositoryInfoDto, UpdateRepositoryDto,
    WarehouseCreate, WarehouseResponse, WarehouseUpdate
)
from app.tasks.warehouse_tasks import process_warehouse_task, reset_warehouse_task
from app.utils.auth import check_user_permission, get_current_user_id
from app.utils.git_utils import GitUtils


logger = logging.getLogger(__name__)

class WarehouseService:
    """仓库服务类，负责仓库管理的核心业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    async def check_warehouse_access(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """检查用户对指定仓库的访问权限"""
        # 管理员有所有权限
        if is_admin:
            return True
            
        # 检查仓库是否存在权限分配
        has_permission_assignment = self.db.query(WarehouseInRole).filter(
            WarehouseInRole.warehouse_id == warehouse_id
        ).first() is not None
        
        # 如果仓库没有权限分配，则是公共仓库，所有人都可以访问
        if not has_permission_assignment:
            return True
            
        # 如果用户未登录，无法访问有权限分配的仓库
        if not current_user_id:
            return False
            
        # 获取用户的角色ID列表
        user_role_ids = self.db.query(UserInRole.role_id).filter(
            UserInRole.user_id == current_user_id
        ).all()
        user_role_ids = [role_id[0] for role_id in user_role_ids]
        
        # 如果用户没有任何角色，无法访问有权限分配的仓库
        if not user_role_ids:
            return False
            
        # 检查用户角色是否有该仓库的权限
        return self.db.query(WarehouseInRole).filter(
            and_(
                WarehouseInRole.warehouse_id == warehouse_id,
                WarehouseInRole.role_id.in_(user_role_ids)
            )
        ).first() is not None
    
    async def check_warehouse_manage_access(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """检查用户对指定仓库的管理权限"""
        # 管理员有所有权限
        if is_admin:
            return True
            
        # 如果用户未登录，无管理权限
        if not current_user_id:
            return False
            
        # 检查仓库是否存在权限分配
        has_permission_assignment = self.db.query(WarehouseInRole).filter(
            WarehouseInRole.warehouse_id == warehouse_id
        ).first() is not None
        
        # 如果仓库没有权限分配，只有管理员可以管理
        if not has_permission_assignment:
            return False
            
        # 获取用户的角色ID列表
        user_role_ids = self.db.query(UserInRole.role_id).filter(
            UserInRole.user_id == current_user_id
        ).all()
        user_role_ids = [role_id[0] for role_id in user_role_ids]
        
        # 如果用户没有任何角色，无管理权限
        if not user_role_ids:
            return False
            
        # 检查用户角色是否有该仓库的写入或删除权限（管理权限）
        return self.db.query(WarehouseInRole).filter(
            and_(
                WarehouseInRole.warehouse_id == warehouse_id,
                WarehouseInRole.role_id.in_(user_role_ids),
                or_(WarehouseInRole.is_write == True, WarehouseInRole.is_delete == True)
            )
        ).first() is not None
    
    def get_warehouses(self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, 
                      current_user_id: Optional[str] = None, is_admin: bool = False) -> Dict[str, Any]:
        """获取仓库列表"""
        query = self.db.query(Warehouse).filter(
            or_(Warehouse.status == WarehouseStatus.COMPLETED, Warehouse.status == WarehouseStatus.PROCESSING)
        )
        
        # 关键词搜索
        if keyword:
            keyword = keyword.strip().lower()
            query = query.filter(
                or_(
                    Warehouse.name.ilike(f"%{keyword}%"),
                    Warehouse.address.ilike(f"%{keyword}%"),
                    Warehouse.description.ilike(f"%{keyword}%")
                )
            )
        
        # 权限过滤
        if not is_admin and current_user_id:
            # 获取用户的角色ID列表
            user_role_ids = self.db.query(UserInRole.role_id).filter(
                UserInRole.user_id == current_user_id
            ).all()
            user_role_ids = [role_id[0] for role_id in user_role_ids]
            
            if not user_role_ids:
                # 用户没有任何角色，只能看到公共仓库
                public_warehouse_ids = self.db.query(Warehouse.id).filter(
                    ~self.db.query(WarehouseInRole).filter(
                        WarehouseInRole.warehouse_id == Warehouse.id
                    ).exists()
                ).all()
                public_warehouse_ids = [warehouse_id[0] for warehouse_id in public_warehouse_ids]
                query = query.filter(Warehouse.id.in_(public_warehouse_ids))
            else:
                # 用户可以访问的仓库：
                # 1. 通过角色权限可以访问的仓库
                # 2. 没有任何权限分配的公共仓库
                accessible_warehouse_ids = self.db.query(WarehouseInRole.warehouse_id).filter(
                    WarehouseInRole.role_id.in_(user_role_ids)
                ).distinct().all()
                accessible_warehouse_ids = [warehouse_id[0] for warehouse_id in accessible_warehouse_ids]
                
                public_warehouse_ids = self.db.query(Warehouse.id).filter(
                    ~self.db.query(WarehouseInRole).filter(
                        WarehouseInRole.warehouse_id == Warehouse.id
                    ).exists()
                ).all()
                public_warehouse_ids = [warehouse_id[0] for warehouse_id in public_warehouse_ids]
                
                all_accessible_ids = list(set(accessible_warehouse_ids + public_warehouse_ids))
                query = query.filter(Warehouse.id.in_(all_accessible_ids))
        elif not current_user_id:
            # 未登录用户只能看到公共仓库
            public_warehouse_ids = self.db.query(Warehouse.id).filter(
                ~self.db.query(WarehouseInRole).filter(
                    WarehouseInRole.warehouse_id == Warehouse.id
                ).exists()
            ).all()
            public_warehouse_ids = [warehouse_id[0] for warehouse_id in public_warehouse_ids]
            query = query.filter(Warehouse.id.in_(public_warehouse_ids))
        
        # 按仓库名称和组织名称分组，保持排序一致性
        total = query.count()
        
        # 排序：先按推荐状态，再按完成状态，最后按创建时间
        warehouses = query.order_by(
            Warehouse.is_recommended.desc(),
            Warehouse.status.desc(),
            Warehouse.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        # 转换为DTO
        warehouse_dtos = []
        for warehouse in warehouses:
            warehouse_dto = RepositoryInfoDto(
                id=warehouse.id,
                name=warehouse.name,
                organization_name=warehouse.organization_name,
                address=warehouse.address,
                description=warehouse.description,
                status=warehouse.status.value,
                type=warehouse.type.value,
                branch=warehouse.branch,
                version=warehouse.version,
                is_recommended=warehouse.is_recommended,
                created_at=warehouse.created_at,
                updated_at=warehouse.updated_at
            )
            warehouse_dtos.append(warehouse_dto)
        
        return {
            "items": warehouse_dtos,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def get_warehouse_by_id(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> Optional[Warehouse]:
        """根据ID获取仓库"""
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        
        if not warehouse:
            return None
            
        # 检查访问权限
        if not self.check_warehouse_access(warehouse_id, current_user_id, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问此仓库"
            )
            
        return warehouse
    
    def create_warehouse(self, create_dto: CreateRepositoryDto, current_user_id: str) -> RepositoryInfoDto:
        """创建仓库
        
        Args:
            create_dto: 创建仓库请求
            current_user_id: 当前用户ID
        """
        # URL解码参数
        decoded_organization = urllib.parse.unquote(create_dto.organization.strip().lower())
        decoded_repository_name = urllib.parse.unquote(create_dto.repository_name.strip().lower())
        
        # 检查仓库是否已存在
        existing_warehouse = self.db.query(Warehouse).filter(
            and_(
                Warehouse.organization_name == decoded_organization,
                Warehouse.name == decoded_repository_name,
                Warehouse.branch == create_dto.branch
            )
        ).first()
        
        if existing_warehouse:
            if existing_warehouse.status == WarehouseStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该名称渠道已存在且处于完成状态，不可重复创建"
                )
            elif existing_warehouse.status == WarehouseStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该名称渠道已存在且处于待处理状态，请等待处理完成"
                )
            elif existing_warehouse.status == WarehouseStatus.PROCESSING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该名称渠道已存在且正在处理中，请稍后再试"
                )
        
        # 检查分支是否已存在
        if create_dto.branch:
            existing_branch = self.db.query(Warehouse).filter(
                and_(
                    Warehouse.branch == create_dto.branch,
                    Warehouse.organization_name == decoded_organization,
                    Warehouse.name == decoded_repository_name
                )
            ).first()
            
            if existing_branch and existing_branch.status in [WarehouseStatus.COMPLETED, WarehouseStatus.PROCESSING]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该分支已经存在"
                )
        
        # 删除旧的仓库（如果存在）
        self.db.query(Warehouse).filter(
            and_(
                Warehouse.organization_name == decoded_organization,
                Warehouse.name == decoded_repository_name,
                Warehouse.branch == create_dto.branch
            )
        ).delete()
        
        # 创建新仓库
        warehouse = Warehouse(
            id=self._generate_warehouse_id(),
            organization_name=decoded_organization,
            name=decoded_repository_name,
            address=create_dto.address,
            description="",
            version="",
            error="",
            prompt="",
            branch=create_dto.branch,
            type=WarehouseType.GIT,
            git_user_name=create_dto.git_user_name,
            git_password=create_dto.git_password,
            email=create_dto.email,
            status=WarehouseStatus.PENDING,
            creator_id=current_user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(warehouse)
        self.db.commit()
        self.db.refresh(warehouse)
        
        # 提交后台处理任务
        try:
            process_warehouse_task.delay(warehouse.id)
            logger.info(f"提交仓库处理任务: {warehouse.id}")
        except Exception as e:
            logger.error(f"提交仓库处理任务失败: {warehouse.id}, 错误: {e}")
        
        # 转换为DTO
        warehouse_dto = RepositoryInfoDto(
            id=warehouse.id,
            name=warehouse.name,
            organization_name=warehouse.organization_name,
            address=warehouse.address,
            description=warehouse.description,
            status=warehouse.status.value,
            type=warehouse.type.value,
            branch=warehouse.branch,
            version=warehouse.version,
            is_recommended=warehouse.is_recommended,
            created_at=warehouse.created_at,
            updated_at=warehouse.updated_at
        )
        
        return warehouse_dto
    
    def update_warehouse(self, warehouse_id: str, update_dto: UpdateRepositoryDto, 
                        current_user_id: Optional[str] = None, is_admin: bool = False) -> RepositoryInfoDto:
        """更新仓库"""
        # 检查管理权限
        if not self.check_warehouse_manage_access(warehouse_id, current_user_id, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理此仓库"
            )
        
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        # 更新仓库信息
        if update_dto.description is not None:
            warehouse.description = update_dto.description
        
        if update_dto.is_recommended is not None:
            warehouse.is_recommended = update_dto.is_recommended
        
        if update_dto.prompt is not None:
            warehouse.prompt = update_dto.prompt
        
        warehouse.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(warehouse)
        
        # 转换为DTO
        warehouse_dto = RepositoryInfoDto(
            id=warehouse.id,
            name=warehouse.name,
            organization_name=warehouse.organization_name,
            address=warehouse.address,
            description=warehouse.description,
            status=warehouse.status.value,
            type=warehouse.type.value,
            branch=warehouse.branch,
            version=warehouse.version,
            is_recommended=warehouse.is_recommended,
            created_at=warehouse.created_at,
            updated_at=warehouse.updated_at
        )
        
        return warehouse_dto
    
    def delete_warehouse(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """删除仓库"""
        # 检查管理权限
        if not self.check_warehouse_manage_access(warehouse_id, current_user_id, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理此仓库"
            )
        
        # 删除仓库
        self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).delete()
        
        # 删除相关文档
        from models.document import Document
        documents = self.db.query(Document).filter(Document.warehouse_id == warehouse_id).all()
        
        for document in documents:
            try:
                import shutil
                import os
                if os.path.exists(document.git_path):
                    shutil.rmtree(document.git_path)
            except Exception as e:
                logger.error(f"删除仓库文件失败: {e}")
        
        self.db.query(Document).filter(Document.warehouse_id == warehouse_id).delete()
        
        # 删除文档目录
        from models.document_catalog import DocumentCatalog
        self.db.query(DocumentCatalog).filter(DocumentCatalog.warehouse_id == warehouse_id).delete()
        
        self.db.commit()
        
        return True
    
    def reset_warehouse(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """重新处理仓库"""
        # 检查管理权限
        if not self.check_warehouse_manage_access(warehouse_id, current_user_id, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理此仓库"
            )
        
        # 更新仓库状态为待处理
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        warehouse.status = WarehouseStatus.PENDING
        warehouse.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # 提交后台重置任务
        try:
            reset_warehouse_task.delay(warehouse_id)
            logger.info(f"提交仓库重置任务: {warehouse_id}")
        except Exception as e:
            logger.error(f"提交仓库重置任务失败: {warehouse_id}, 错误: {e}")
        
        return True
    
    def update_warehouse_status(self, warehouse_id: str, current_user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """更新仓库状态"""
        # 检查管理权限
        if not self.check_warehouse_manage_access(warehouse_id, current_user_id, is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理此仓库"
            )
        
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        warehouse.status = WarehouseStatus.PENDING
        warehouse.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def get_last_warehouse(self, address: str) -> Optional[Dict[str, Any]]:
        """查询上次提交的仓库"""
        address = address.strip().rstrip('/').lower()
        
        # 判断是否.git结束，如果不是需要添加
        if not address.endswith('.git'):
            address += '.git'
        
        warehouse = self.db.query(Warehouse).filter(Warehouse.address == address).first()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return {
            "name": warehouse.name,
            "address": warehouse.address,
            "description": warehouse.description,
            "version": warehouse.version,
            "status": warehouse.status.value,
            "error": warehouse.error
        }
    
    def _generate_warehouse_id(self) -> str:
        """生成仓库ID"""
        import uuid
        return str(uuid.uuid4()) 