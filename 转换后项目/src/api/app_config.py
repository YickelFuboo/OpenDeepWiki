from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.dto.app_config_dto import (
    AppConfigInput, AppConfigOutput, DomainValidationRequest, DomainValidationResponse
)
from src.services.app_config_service import AppConfigService
from src.models.user import User

app_config_router = APIRouter()


@app_config_router.post("/", response_model=AppConfigOutput)
@require_user()
async def create_app_config(
    app_config_data: AppConfigInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建应用配置"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.create_app_config(current_user.id, app_config_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建应用配置失败: {str(e)}"
        )


@app_config_router.get("/", response_model=List[AppConfigOutput])
@require_user()
async def get_app_configs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取应用配置列表"""
    app_config_service = AppConfigService(db)
    
    try:
        return await app_config_service.get_app_configs(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用配置列表失败: {str(e)}"
        )


@app_config_router.get("/{app_id}", response_model=AppConfigOutput)
@require_user()
async def get_app_config_by_id(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据AppId获取应用配置"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.get_app_config_by_id(current_user.id, app_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="应用配置不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用配置失败: {str(e)}"
        )


@app_config_router.put("/{app_id}", response_model=AppConfigOutput)
@require_user()
async def update_app_config(
    app_id: str,
    app_config_data: AppConfigInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新应用配置"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.update_app_config(current_user.id, app_id, app_config_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="应用配置不存在"
            )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新应用配置失败: {str(e)}"
        )


@app_config_router.delete("/{app_id}")
@require_user()
async def delete_app_config(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除应用配置"""
    app_config_service = AppConfigService(db)
    
    try:
        success = await app_config_service.delete_app_config(current_user.id, app_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="应用配置不存在"
            )
        return {"message": "删除成功", "code": 200}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除应用配置失败: {str(e)}"
        )


@app_config_router.post("/{app_id}/toggle", response_model=AppConfigOutput)
@require_user()
async def toggle_app_config_enabled(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """切换应用配置启用状态"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.toggle_app_config_enabled(current_user.id, app_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="应用配置不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换应用配置状态失败: {str(e)}"
        )


@app_config_router.post("/validatedomain", response_model=DomainValidationResponse)
async def validate_domain(
    request: DomainValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """验证域名（公开接口）"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.validate_domain(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证域名失败: {str(e)}"
        )


@app_config_router.get("/public/{app_id}", response_model=Optional[AppConfigOutput])
async def get_public_config(
    app_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取公开的应用配置"""
    app_config_service = AppConfigService(db)
    
    try:
        result = await app_config_service.get_public_config(app_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公开应用配置失败: {str(e)}"
        ) 