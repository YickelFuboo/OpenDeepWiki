from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.user_in_role import UserInRole
from src.models.warehouse_in_role import WarehouseInRole
from src.dto.warehouse_dto import WarehouseDto
from src.dto.page_dto import PageDto


class WarehouseListService:
    """仓库列表服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_warehouse_list(
        self, 
        page: int, 
        page_size: int, 
        keyword: str = "",
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> PageDto[WarehouseDto]:
        """获取仓库列表"""
        try:
            # 基础查询
            query = select(Warehouse).where(
                Warehouse.status.in_(["completed", "processing"])
            )
            
            # 关键词搜索
            if keyword.strip():
                keyword = keyword.strip().lower()
                query = query.where(
                    Warehouse.name.contains(keyword) | 
                    Warehouse.address.contains(keyword) |
                    Warehouse.description.contains(keyword)
                )
            
            # 权限过滤
            if not is_admin and user_id:
                # 获取用户的角色ID列表
                user_roles_result = await self.db.execute(
                    select(UserInRole.role_id).where(UserInRole.user_id == user_id)
                )
                user_role_ids = [row[0] for row in user_roles_result.fetchall()]
                
                if user_role_ids:
                    # 获取用户角色有权限的仓库
                    accessible_warehouse_ids_result = await self.db.execute(
                        select(WarehouseInRole.warehouse_id).where(
                            WarehouseInRole.role_id.in_(user_role_ids)
                        )
                    )
                    accessible_warehouse_ids = [row[0] for row in accessible_warehouse_ids_result.fetchall()]
                    
                    # 获取公共仓库（没有权限分配的仓库）
                    public_warehouse_ids_result = await self.db.execute(
                        select(Warehouse.id).where(
                            ~Warehouse.id.in_(
                                select(WarehouseInRole.warehouse_id)
                            )
                        )
                    )
                    public_warehouse_ids = [row[0] for row in public_warehouse_ids_result.fetchall()]
                    
                    # 合并所有可访问的仓库ID
                    all_accessible_ids = list(set(accessible_warehouse_ids + public_warehouse_ids))
                    
                    if all_accessible_ids:
                        query = query.where(Warehouse.id.in_(all_accessible_ids))
                    else:
                        # 如果用户没有任何可访问的仓库，返回空列表
                        return PageDto[WarehouseDto](total=0, items=[])
            
            # 计算总数
            count_query = select(func.count(Warehouse.id)).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # 分页查询
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await self.db.execute(query)
            warehouses = result.scalars().all()
            
            # 转换为DTO
            warehouse_dtos = []
            for warehouse in warehouses:
                warehouse_dto = WarehouseDto(
                    id=warehouse.id,
                    name=warehouse.name,
                    description=warehouse.description,
                    address=warehouse.address,
                    organization_name=warehouse.organization_name,
                    branch=warehouse.branch,
                    status=warehouse.status,
                    type=warehouse.type,
                    is_public=warehouse.is_public,
                    document_count=warehouse.document_count,
                    view_count=warehouse.view_count,
                    created_at=warehouse.created_at,
                    updated_at=warehouse.updated_at
                )
                warehouse_dtos.append(warehouse_dto)
            
            return PageDto[WarehouseDto](total=total, items=warehouse_dtos)
            
        except Exception as e:
            logger.error(f"获取仓库列表失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取仓库列表失败: {str(e)}")
    
    async def get_last_warehouse(self, address: str) -> Dict[str, Any]:
        """查询上次提交的仓库"""
        try:
            address = address.strip().rstrip('/').lower()
            
            # 判断是否.git结束，如果不是需要添加
            if not address.endswith(".git"):
                address += ".git"
            
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.address == address)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            return {
                "name": warehouse.name,
                "address": warehouse.address,
                "description": warehouse.description,
                "version": warehouse.version,
                "status": warehouse.status,
                "error": warehouse.error
            }
            
        except Exception as e:
            logger.error(f"查询上次提交的仓库失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询上次提交的仓库失败: {str(e)}")
    
    async def get_change_log(self, owner: str, name: str) -> Optional[Dict[str, Any]]:
        """获取变更日志"""
        try:
            owner = owner.strip().lower()
            name = name.strip().lower()
            
            result = await self.db.execute(
                select(Warehouse).where(
                    Warehouse.name == name,
                    Warehouse.organization_name == owner,
                    Warehouse.status.in_(["completed", "processing"])
                )
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(
                    status_code=404, 
                    detail=f"仓库不存在，请检查仓库名称和组织名称: {owner} {name}"
                )
            
            # 获取提交记录
            from src.models.document_commit_record import DocumentCommitRecord
            commit_result = await self.db.execute(
                select(DocumentCommitRecord).where(DocumentCommitRecord.warehouse_id == warehouse.id)
            )
            commits = commit_result.scalars().all()
            
            # 构建变更日志
            change_log = []
            for commit in commits:
                change_log.append(f"## {commit.last_update} {commit.title}")
                change_log.append(f" {commit.commit_message}")
            
            return {
                "commit_id": "",
                "commit_message": "\n".join(change_log),
                "created_at": warehouse.created_at
            }
            
        except Exception as e:
            logger.error(f"获取变更日志失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取变更日志失败: {str(e)}")
    
    async def update_warehouse_status(self, warehouse_id: str, user_id: str) -> bool:
        """更新仓库状态"""
        try:
            # 检查管理权限
            from src.services.warehouse_permission_service import WarehousePermissionService
            permission_service = WarehousePermissionService(self.db)
            if not await permission_service.check_warehouse_manage_access(warehouse_id, user_id):
                raise HTTPException(status_code=403, detail="您没有权限管理此仓库")
            
            # 更新仓库状态为待处理
            from sqlalchemy import update
            await self.db.execute(
                update(Warehouse)
                .where(Warehouse.id == warehouse_id)
                .values(status="pending")
            )
            await self.db.commit()
            
            logger.info(f"Updated warehouse status: {warehouse_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新仓库状态失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"更新仓库状态失败: {str(e)}") 