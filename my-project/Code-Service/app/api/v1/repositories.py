from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.connection import get_db
from app.repositories.services.warehouse_service import WarehouseService
from app.schemas.warehouse import (
    CreateRepositoryDto, UpdateRepositoryDto, RepositoryInfoDto,
    WarehouseResponse, WarehouseInRoleCreate, WarehouseInRoleUpdate, WarehouseInRoleResponse
)
from app.schemas.common import BaseResponse, PaginationParams, PaginatedResponse
from app.utils.auth import get_current_active_user, get_current_user_id, check_user_permission
from app.db.models.user import User

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
        
        warehouse = warehouse_service.create_warehouse(create_dto, current_user.id)
        return RepositoryInfoDto.from_orm(warehouse)
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
        
        # 检查用户是否有更新仓库的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限更新仓库"
            )
        
        warehouse = warehouse_service.update_warehouse(warehouse_id, update_dto)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return RepositoryInfoDto.from_orm(warehouse)
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
        
        # 检查用户是否有删除仓库的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限删除仓库"
            )
        
        success = warehouse_service.delete_warehouse(warehouse_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return BaseResponse(
            success=True,
            message="删除仓库成功"
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
    """重置仓库"""
    try:
        warehouse_service = WarehouseService(db)
        
        # 检查用户是否有重置仓库的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限重置仓库"
            )
        
        success = warehouse_service.reset_warehouse(warehouse_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return BaseResponse(
            success=True,
            message="重置仓库成功"
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
        
        # 检查用户是否有更新仓库状态的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限更新仓库状态"
            )
        
        success = warehouse_service.update_warehouse_status(warehouse_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return BaseResponse(
            success=True,
            message="更新仓库状态成功"
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
    """根据地址获取最新的仓库"""
    try:
        warehouse_service = WarehouseService(db)
        warehouse = warehouse_service.get_last_warehouse_by_address(address)
        
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
            detail=f"获取仓库失败: {str(e)}"
        )

@router.post("/{warehouse_id}/roles", response_model=WarehouseInRoleResponse)
async def create_warehouse_role(
    warehouse_id: str,
    role_dto: WarehouseInRoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """为仓库创建角色"""
    try:
        warehouse_service = WarehouseService(db)
        
        # 检查用户是否有管理仓库角色的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库角色"
            )
        
        warehouse_role = warehouse_service.create_warehouse_role(warehouse_id, role_dto)
        if not warehouse_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return WarehouseInRoleResponse.from_orm(warehouse_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建仓库角色失败: {str(e)}"
        )

@router.put("/{warehouse_id}/roles/{role_id}", response_model=WarehouseInRoleResponse)
async def update_warehouse_role(
    warehouse_id: str,
    role_id: str,
    role_dto: WarehouseInRoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新仓库角色"""
    try:
        warehouse_service = WarehouseService(db)
        
        # 检查用户是否有管理仓库角色的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库角色"
            )
        
        warehouse_role = warehouse_service.update_warehouse_role(warehouse_id, role_id, role_dto)
        if not warehouse_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库角色不存在"
            )
        
        return WarehouseInRoleResponse.from_orm(warehouse_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新仓库角色失败: {str(e)}"
        )

@router.delete("/{warehouse_id}/roles/{role_id}")
async def delete_warehouse_role(
    warehouse_id: str,
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除仓库角色"""
    try:
        warehouse_service = WarehouseService(db)
        
        # 检查用户是否有管理仓库角色的权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理仓库角色"
            )
        
        success = warehouse_service.delete_warehouse_role(warehouse_id, role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库角色不存在"
            )
        
        return BaseResponse(
            success=True,
            message="删除仓库角色成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除仓库角色失败: {str(e)}"
        ) 