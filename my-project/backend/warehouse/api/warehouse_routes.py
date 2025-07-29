from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database import get_db
from warehouse.services.warehouse_service import WarehouseService
from schemas.warehouse import (
    CreateRepositoryDto, UpdateRepositoryDto, RepositoryInfoDto,
    WarehouseResponse, WarehouseInRoleCreate, WarehouseInRoleUpdate, WarehouseInRoleResponse
)
from schemas.common import BaseResponse, PaginationParams, PaginatedResponse
from utils.auth import get_current_active_user, get_current_user_id, check_user_permission
from models.user import User

router = APIRouter(prefix="/warehouses", tags=["仓库管理"])

@router.get("/", response_model=PaginatedResponse)
async def get_warehouses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仓库列表"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id if current_user else None
        is_admin = check_user_permission(current_user, "admin") if current_user else False
        
        result = warehouse_service.get_warehouses(
            page=page,
            page_size=page_size,
            keyword=keyword,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        return PaginatedResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仓库列表失败: {str(e)}"
        )

@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仓库详情"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id if current_user else None
        is_admin = check_user_permission(current_user, "admin") if current_user else False
        
        warehouse = warehouse_service.get_warehouse_by_id(
            warehouse_id=warehouse_id,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return WarehouseResponse.from_orm(warehouse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仓库详情失败: {str(e)}"
        )

@router.post("/", response_model=RepositoryInfoDto)
async def create_warehouse(
    create_dto: CreateRepositoryDto,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建仓库"""
    try:
        warehouse_service = WarehouseService(db)
        
        # 检查用户是否有创建仓库的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限创建仓库"
            )
        
        warehouse_dto = warehouse_service.create_warehouse(
            create_dto=create_dto,
            current_user_id=current_user.id
        )
        
        return warehouse_dto
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建仓库失败: {str(e)}"
        )

@router.put("/{warehouse_id}", response_model=RepositoryInfoDto)
async def update_warehouse(
    warehouse_id: str,
    update_dto: UpdateRepositoryDto,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新仓库"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id
        is_admin = check_user_permission(current_user, "admin")
        
        warehouse_dto = warehouse_service.update_warehouse(
            warehouse_id=warehouse_id,
            update_dto=update_dto,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        return warehouse_dto
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新仓库失败: {str(e)}"
        )

@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除仓库"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id
        is_admin = check_user_permission(current_user, "admin")
        
        success = warehouse_service.delete_warehouse(
            warehouse_id=warehouse_id,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        if success:
            return BaseResponse(message="仓库删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="仓库删除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除仓库失败: {str(e)}"
        )

@router.post("/{warehouse_id}/reset")
async def reset_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重新处理仓库"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id
        is_admin = check_user_permission(current_user, "admin")
        
        success = warehouse_service.reset_warehouse(
            warehouse_id=warehouse_id,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        if success:
            return BaseResponse(message="仓库重置成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="仓库重置失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置仓库失败: {str(e)}"
        )

@router.post("/{warehouse_id}/status")
async def update_warehouse_status(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新仓库状态"""
    try:
        warehouse_service = WarehouseService(db)
        current_user_id = current_user.id
        is_admin = check_user_permission(current_user, "admin")
        
        success = warehouse_service.update_warehouse_status(
            warehouse_id=warehouse_id,
            current_user_id=current_user_id,
            is_admin=is_admin
        )
        
        if success:
            return BaseResponse(message="仓库状态更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="仓库状态更新失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新仓库状态失败: {str(e)}"
        )

@router.get("/last/{address}")
async def get_last_warehouse(
    address: str,
    db: Session = Depends(get_db)
):
    """查询上次提交的仓库"""
    try:
        warehouse_service = WarehouseService(db)
        
        result = warehouse_service.get_last_warehouse(address=address)
        
        return BaseResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询仓库失败: {str(e)}"
        )

# 仓库角色权限管理
@router.post("/{warehouse_id}/roles", response_model=WarehouseInRoleResponse)
async def create_warehouse_role(
    warehouse_id: str,
    role_dto: WarehouseInRoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """为仓库分配角色权限"""
    try:
        # 检查用户是否有管理权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库权限"
            )
        
        from models.warehouse import WarehouseInRole
        
        # 检查是否已存在相同的权限分配
        existing_role = db.query(WarehouseInRole).filter(
            and_(
                WarehouseInRole.warehouse_id == warehouse_id,
                WarehouseInRole.role_id == role_dto.role_id
            )
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该角色已分配到此仓库"
            )
        
        # 创建新的权限分配
        warehouse_role = WarehouseInRole(
            warehouse_id=warehouse_id,
            role_id=role_dto.role_id,
            is_read=role_dto.is_read,
            is_write=role_dto.is_write,
            is_delete=role_dto.is_delete
        )
        
        db.add(warehouse_role)
        db.commit()
        db.refresh(warehouse_role)
        
        return WarehouseInRoleResponse.from_orm(warehouse_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配仓库权限失败: {str(e)}"
        )

@router.put("/{warehouse_id}/roles/{role_id}", response_model=WarehouseInRoleResponse)
async def update_warehouse_role(
    warehouse_id: str,
    role_id: str,
    role_dto: WarehouseInRoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新仓库角色权限"""
    try:
        # 检查用户是否有管理权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库权限"
            )
        
        from models.warehouse import WarehouseInRole
        from sqlalchemy import and_
        
        warehouse_role = db.query(WarehouseInRole).filter(
            and_(
                WarehouseInRole.warehouse_id == warehouse_id,
                WarehouseInRole.role_id == role_id
            )
        ).first()
        
        if not warehouse_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库角色权限不存在"
            )
        
        # 更新权限
        if role_dto.is_read is not None:
            warehouse_role.is_read = role_dto.is_read
        if role_dto.is_write is not None:
            warehouse_role.is_write = role_dto.is_write
        if role_dto.is_delete is not None:
            warehouse_role.is_delete = role_dto.is_delete
        
        db.commit()
        db.refresh(warehouse_role)
        
        return WarehouseInRoleResponse.from_orm(warehouse_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新仓库权限失败: {str(e)}"
        )

@router.delete("/{warehouse_id}/roles/{role_id}")
async def delete_warehouse_role(
    warehouse_id: str,
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除仓库角色权限"""
    try:
        # 检查用户是否有管理权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库权限"
            )
        
        from models.warehouse import WarehouseInRole
        from sqlalchemy import and_
        
        warehouse_role = db.query(WarehouseInRole).filter(
            and_(
                WarehouseInRole.warehouse_id == warehouse_id,
                WarehouseInRole.role_id == role_id
            )
        ).first()
        
        if not warehouse_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库角色权限不存在"
            )
        
        db.delete(warehouse_role)
        db.commit()
        
        return BaseResponse(message="仓库权限删除成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除仓库权限失败: {str(e)}"
        ) 