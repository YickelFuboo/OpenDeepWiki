from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import io

from app.core.database import get_db
from app.core.simple_auth import get_current_user, SimpleUserContext

from app.services.warehouse_service import WarehouseService
from src.services.warehouse_permission_service import WarehousePermissionService
from src.services.warehouse_upload_service import WarehouseUploadService
from src.services.warehouse_content_service import WarehouseContentService
from src.services.warehouse_list_service import WarehouseListService
from src.dto.warehouse_dto import (
    CreateWarehouseDto, 
    UpdateWarehouseDto, 
    WarehouseInfoDto,
    WarehouseListResponse
)
from src.dto.page_dto import PageDto

router = APIRouter(prefix="/api/warehouse", tags=["仓库管理"])


# 基础CRUD操作
@router.post("/", response_model=WarehouseInfoDto)
async def create_warehouse(
    create_dto: CreateWarehouseDto,
    db: AsyncSession = Depends(get_db),
    current_user: SimpleUserContext = Depends(get_current_user)
):
    """创建仓库"""
    warehouse_service = WarehouseService(db)
    warehouse = await warehouse_service.create_warehouse(current_user.id, create_dto)
    return warehouse_service.warehouse_to_dto(warehouse)


@router.get("/{warehouse_id}", response_model=WarehouseInfoDto)
async def get_warehouse(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: SimpleUserContext = Depends(get_current_user)
):
    """获取仓库详情"""
    warehouse_service = WarehouseService(db)
    warehouse = await warehouse_service.get_warehouse_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse_service.warehouse_to_dto(warehouse)


@router.put("/{warehouse_id}", response_model=WarehouseInfoDto)
async def update_warehouse(
    warehouse_id: str,
    update_dto: UpdateWarehouseDto,
    db: AsyncSession = Depends(get_db),
    current_user: SimpleUserContext = Depends(get_current_user)
):
    """更新仓库"""
    warehouse_service = WarehouseService(db)
    warehouse = await warehouse_service.update_warehouse(warehouse_id, current_user.id, update_dto)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在或无权限")
    return warehouse_service.warehouse_to_dto(warehouse)


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: SimpleUserContext = Depends(get_current_user)
):
    """删除仓库"""
    warehouse_service = WarehouseService(db)
    success = await warehouse_service.delete_warehouse(warehouse_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="仓库不存在或无权限")
    return {"message": "仓库删除成功"}


# 权限相关操作
@router.get("/{warehouse_id}/permission/check")
async def check_warehouse_permission(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: SimpleUserContext = Depends(get_current_user)
):
    """检查仓库权限"""
    permission_service = WarehousePermissionService(db)
    has_access = await permission_service.check_warehouse_access(warehouse_id, current_user.id)
    has_manage = await permission_service.check_warehouse_manage_access(warehouse_id, current_user.id)
    
    return {
        "has_access": has_access,
        "has_manage": has_manage
    }


# 上传相关操作
@router.post("/upload")
async def upload_warehouse(
    organization: str = Form(...),
    repository_name: str = Form(...),
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """上传仓库"""
    upload_service = WarehouseUploadService(db)
    return await upload_service.upload_and_submit_warehouse(
        organization=organization,
        repository_name=repository_name,
        user_id="default",
        file=file,
        file_url=file_url
    )


@router.post("/{warehouse_id}/submit")
async def submit_warehouse(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    """提交仓库处理"""
    upload_service = WarehouseUploadService(db)
    return await upload_service.submit_warehouse(warehouse_id, "default")


@router.post("/custom-submit")
async def custom_submit_warehouse(
    organization: str = Form(...),
    repository_name: str = Form(...),
    git_url: str = Form(...),
    branch: str = Form("main"),
    db: AsyncSession = Depends(get_db)
):
    """自定义提交仓库"""
    upload_service = WarehouseUploadService(db)
    return await upload_service.custom_submit_warehouse(
        organization=organization,
        repository_name=repository_name,
        git_url=git_url,
        branch=branch,
        user_id="default"
    )


# 内容相关操作
@router.get("/{warehouse_id}/file")
async def get_file_content(
    warehouse_id: str,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件内容"""
    content_service = WarehouseContentService(db)
    content = await content_service.get_file_content(warehouse_id, path, current_user.id)
    return {"content": content}


@router.get("/file/content")
async def get_file_content_line(
    organization_name: str = Query(...),
    name: str = Query(...),
    file_path: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """获取指定组织的文件内容"""
    content_service = WarehouseContentService(db)
    content = await content_service.get_file_content_line(organization_name, name, file_path)
    return {"content": content}


@router.get("/{warehouse_id}/export")
async def export_markdown_zip(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出Markdown压缩包"""
    content_service = WarehouseContentService(db)
    zip_data = await content_service.export_markdown_zip(warehouse_id, current_user.id)
    
    return StreamingResponse(
        io.BytesIO(zip_data),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=warehouse_{warehouse_id}.zip"}
    )


@router.get("/overview")
async def get_warehouse_overview(
    owner: str = Query(...),
    name: str = Query(...),
    branch: str = Query("main"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仓库概述"""
    content_service = WarehouseContentService(db)
    return await content_service.get_warehouse_overview(
        owner=owner,
        name=name,
        branch=branch,
        user_id=current_user.id
    )


@router.get("/mini-map")
async def get_mini_map(
    owner: str = Query(...),
    name: str = Query(...),
    branch: str = Query(""),
    db: AsyncSession = Depends(get_db)
):
    """获取思维导图"""
    content_service = WarehouseContentService(db)
    return await content_service.get_mini_map(owner, name, branch)


# 列表相关操作
@router.get("/", response_model=PageDto[WarehouseInfoDto])
async def get_warehouse_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仓库列表"""
    list_service = WarehouseListService(db)
    return await list_service.get_warehouse_list(
        page=page,
        page_size=page_size,
        keyword=keyword,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )


@router.get("/last")
async def get_last_warehouse(
    address: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """查询上次提交的仓库"""
    list_service = WarehouseListService(db)
    return await list_service.get_last_warehouse(address)


@router.get("/change-log")
async def get_change_log(
    owner: str = Query(...),
    name: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """获取变更日志"""
    list_service = WarehouseListService(db)
    return await list_service.get_change_log(owner, name)


@router.put("/{warehouse_id}/status")
async def update_warehouse_status(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新仓库状态"""
    list_service = WarehouseListService(db)
    success = await list_service.update_warehouse_status(warehouse_id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="更新仓库状态失败")
    return {"message": "仓库状态更新成功"}


# 统计相关操作
@router.get("/{warehouse_id}/view-count")
async def increment_view_count(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    """增加仓库查看次数"""
    warehouse_service = WarehouseService(db)
    await warehouse_service.increment_view_count(warehouse_id)
    return {"message": "查看次数已增加"} 