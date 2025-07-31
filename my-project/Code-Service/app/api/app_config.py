"""
应用配置管理API

提供应用配置的CRUD和域名验证接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.connection import get_db
from app.auth.services.app_config_service import AppConfigService
from app.schemas.app_config import (
    AppConfigInput, AppConfigOutput, DomainValidationRequest, DomainValidationResponse
)
from app.schemas.common import BaseResponse
from app.utils.auth import get_current_active_user
from app.db.models.user import User

router = APIRouter()


@router.post("/", response_model=AppConfigOutput)
async def create_app_config(
    config_data: AppConfigInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建应用配置"""
    try:
        service = AppConfigService(db)
        return service.create_app_config(config_data, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建应用配置失败: {str(e)}"
        )


@router.get("/", response_model=List[AppConfigOutput])
async def get_app_configs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取应用配置列表"""
    try:
        service = AppConfigService(db)
        return service.get_app_configs(current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用配置列表失败: {str(e)}"
        )


@router.get("/{app_id}", response_model=AppConfigOutput)
async def get_app_config_by_app_id(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据AppId获取应用配置"""
    try:
        service = AppConfigService(db)
        return service.get_app_config_by_app_id(app_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用配置失败: {str(e)}"
        )


@router.put("/{app_id}", response_model=AppConfigOutput)
async def update_app_config(
    app_id: str,
    config_data: AppConfigInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新应用配置"""
    try:
        service = AppConfigService(db)
        return service.update_app_config(app_id, config_data, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新应用配置失败: {str(e)}"
        )


@router.delete("/{app_id}")
async def delete_app_config(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除应用配置"""
    try:
        service = AppConfigService(db)
        service.delete_app_config(app_id, current_user.id)
        return BaseResponse(
            success=True,
            message="删除应用配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除应用配置失败: {str(e)}"
        )


@router.post("/{app_id}/toggle", response_model=AppConfigOutput)
async def toggle_app_config_enabled(
    app_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启用/禁用应用"""
    try:
        service = AppConfigService(db)
        return service.toggle_app_config_enabled(app_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换应用状态失败: {str(e)}"
        )


@router.post("/validatedomain", response_model=DomainValidationResponse)
async def validate_domain(
    request: DomainValidationRequest,
    db: Session = Depends(get_db)
):
    """域名验证（公开接口，不需要登录）"""
    try:
        service = AppConfigService(db)
        return service.validate_domain(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"域名验证失败: {str(e)}"
        )


@router.get("/public/{app_id}", response_model=Optional[AppConfigOutput])
async def get_public_app_config(
    app_id: str,
    db: Session = Depends(get_db)
):
    """获取应用配置（公开接口，用于第三方脚本）"""
    try:
        service = AppConfigService(db)
        return service.get_public_app_config(app_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公开应用配置失败: {str(e)}"
        ) 