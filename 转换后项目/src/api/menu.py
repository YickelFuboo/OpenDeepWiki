from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.core.auth import get_current_user
from src.dto.user_dto import UserInfoDto
from src.dto.menu_dto import MenuItemDto, UserMenuDto
from src.core.dependencies import get_menu_service
from src.services.menu_service import MenuService

menu_router = APIRouter()


@menu_router.get("/usermenu", response_model=UserMenuDto)
async def get_user_menu(
    current_user: UserInfoDto = Depends(get_current_user),
    menu_service: MenuService = Depends(get_menu_service)
):
    """获取当前用户的菜单"""
    try:
        return await menu_service.get_user_menu(current_user.id)
    except Exception as ex:
        logger.error(f"获取用户菜单失败: UserId={current_user.id}, Error={ex}")
        raise HTTPException(status_code=500, detail="获取用户菜单失败")


@menu_router.get("/system", response_model=List[MenuItemDto])
async def get_system_menus(
    current_user: UserInfoDto = Depends(get_current_user),
    menu_service: MenuService = Depends(get_menu_service)
):
    """获取系统菜单结构（管理员权限）"""
    try:
        # 检查管理员权限
        if "admin" not in current_user.role:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        return await menu_service.get_system_menus()
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"获取系统菜单失败: UserId={current_user.id}, Error={ex}")
        raise HTTPException(status_code=500, detail="获取系统菜单失败") 