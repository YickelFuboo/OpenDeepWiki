from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.warehouse_service import WarehouseService
from schemas.common import BaseResponse, PaginationParams, PaginatedResponse
from utils.auth import get_current_active_user
from models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_warehouses(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仓库列表"""
    try:
        warehouse_service = WarehouseService(db)
        result = warehouse_service.get_warehouses(pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仓库列表失败: {str(e)}"
        )


@router.get("/{warehouse_id}", response_model=BaseResponse)
async def get_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仓库详情"""
    try:
        warehouse_service = WarehouseService(db)
        warehouse = warehouse_service.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        return BaseResponse(
            success=True,
            message="获取仓库详情成功",
            data=warehouse
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仓库详情失败: {str(e)}"
        )


@router.post("/", response_model=BaseResponse)
async def create_warehouse(
    warehouse_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建仓库"""
    try:
        warehouse_service = WarehouseService(db)
        warehouse = warehouse_service.create_warehouse(warehouse_data, current_user.id)
        return BaseResponse(
            success=True,
            message="创建仓库成功",
            data={"warehouse_id": warehouse.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建仓库失败: {str(e)}"
        )


@router.put("/{warehouse_id}", response_model=BaseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新仓库"""
    try:
        warehouse_service = WarehouseService(db)
        warehouse = warehouse_service.update_warehouse(warehouse_id, warehouse_data)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        return BaseResponse(
            success=True,
            message="更新仓库成功",
            data={"warehouse_id": warehouse.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新仓库失败: {str(e)}"
        )


@router.delete("/{warehouse_id}", response_model=BaseResponse)
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除仓库"""
    try:
        warehouse_service = WarehouseService(db)
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


@router.post("/{warehouse_id}/sync", response_model=BaseResponse)
async def sync_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """同步仓库"""
    try:
        warehouse_service = WarehouseService(db)
        result = warehouse_service.sync_warehouse(warehouse_id)
        return BaseResponse(
            success=True,
            message="仓库同步成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"仓库同步失败: {str(e)}"
        )


@router.get("/{warehouse_id}/files", response_model=BaseResponse)
async def get_warehouse_files(
    warehouse_id: str,
    path: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取仓库文件列表"""
    try:
        warehouse_service = WarehouseService(db)
        files = warehouse_service.get_warehouse_files(warehouse_id, path)
        return BaseResponse(
            success=True,
            message="获取文件列表成功",
            data={"files": files}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {str(e)}"
        )


@router.get("/{warehouse_id}/files/content", response_model=BaseResponse)
async def get_file_content(
    warehouse_id: str,
    file_path: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文件内容"""
    try:
        warehouse_service = WarehouseService(db)
        content = warehouse_service.get_file_content(warehouse_id, file_path)
        return BaseResponse(
            success=True,
            message="获取文件内容成功",
            data={"content": content}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件内容失败: {str(e)}"
        )


@router.post("/{warehouse_id}/analyze", response_model=BaseResponse)
async def analyze_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分析仓库代码"""
    try:
        warehouse_service = WarehouseService(db)
        result = warehouse_service.analyze_warehouse(warehouse_id)
        return BaseResponse(
            success=True,
            message="仓库分析成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"仓库分析失败: {str(e)}"
        ) 