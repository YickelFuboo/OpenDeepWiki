from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.connection import get_db
from services.menu_service import MenuService
from schemas.role import UserMenu, MenuItem
from schemas.common import BaseResponse
from utils.auth import get_current_active_user, check_user_permission
from models.user import User

router = APIRouter()

@router.get("/user-menu", response_model=UserMenu)
async def get_user_menu(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的菜单"""
    try:
        menu_service = MenuService(db)
        user_menu = menu_service.get_user_menu(current_user.id)
        return user_menu
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户菜单失败: {str(e)}"
        )

@router.get("/system-menus", response_model=List[MenuItem])
async def get_system_menus(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统菜单结构（管理员权限）"""
    try:
        # 检查权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问系统菜单"
            )
        
        menu_service = MenuService(db)
        system_menus = menu_service.get_system_menus()
        return system_menus
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统菜单失败: {str(e)}"
        )

@router.get("/check-permission")
async def check_user_path_permission(
    path: str = Query(..., description="要检查的路径"),
    user_id: Optional[str] = Query(None, description="用户ID（可选，默认当前用户）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检查用户是否有访问指定路径的权限"""
    try:
        menu_service = MenuService(db)
        
        # 如果没有指定用户ID，使用当前用户
        target_user_id = user_id or current_user.id
        
        has_permission = menu_service.check_user_path_permission(path, target_user_id)
        
        return BaseResponse(
            data={
                "has_permission": has_permission,
                "path": path,
                "user_id": target_user_id
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户路径权限失败: {str(e)}"
        )

@router.get("/breadcrumb")
async def get_menu_breadcrumb(
    current_path: str = Query(..., description="当前路径"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取菜单面包屑路径"""
    try:
        menu_service = MenuService(db)
        
        # 获取用户菜单
        user_menu = menu_service.get_user_menu(current_user.id)
        
        # 获取面包屑
        breadcrumb = menu_service.get_menu_breadcrumb(user_menu.menus, current_path)
        
        return BaseResponse(data=breadcrumb)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取菜单面包屑失败: {str(e)}"
        )

@router.get("/admin-menu-list", response_model=List[MenuItem])
async def get_admin_menu_list(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取管理员菜单列表（用于权限配置）"""
    try:
        # 检查权限
        if not check_user_permission(current_user, "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问管理员菜单"
            )
        
        menu_service = MenuService(db)
        admin_menus = menu_service.get_admin_menu_list()
        return admin_menus
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取管理员菜单失败: {str(e)}"
        )

@router.get("/flatten-menus")
async def get_flatten_menus(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取扁平化的菜单列表"""
    try:
        menu_service = MenuService(db)
        
        # 获取用户菜单
        user_menu = menu_service.get_user_menu(current_user.id)
        
        # 扁平化菜单
        flattened_menus = menu_service.flatten_menus(user_menu.menus)
        
        return BaseResponse(data=flattened_menus)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取扁平化菜单失败: {str(e)}"
        )

@router.get("/menu-info")
async def get_menu_info(
    path: str = Query(..., description="菜单路径"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定路径的菜单信息"""
    try:
        menu_service = MenuService(db)
        
        # 获取系统菜单结构
        system_menus = menu_service.get_system_menus()
        
        # 查找指定路径的菜单项
        menu_item = menu_service._find_menu_by_path(system_menus, path)
        
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜单项不存在"
            )
        
        # 检查当前用户是否有权限访问
        has_permission = menu_service.check_user_path_permission(path, current_user.id)
        
        return BaseResponse(data={
            "menu_item": menu_item,
            "has_permission": has_permission,
            "is_active": menu_service.is_menu_active(menu_item, path)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取菜单信息失败: {str(e)}"
        )

@router.get("/user-roles")
async def get_user_roles_for_menu(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的角色信息（用于菜单权限判断）"""
    try:
        from services.role_service import RoleService
        role_service = RoleService(db)
        
        user_roles = role_service.get_user_roles(current_user.id)
        
        return BaseResponse(data={
            "user_id": current_user.id,
            "username": current_user.username,
            "roles": user_roles
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户角色失败: {str(e)}"
        )

@router.get("/menu-stats")
async def get_menu_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取菜单统计信息"""
    try:
        menu_service = MenuService(db)
        
        # 获取用户菜单
        user_menu = menu_service.get_user_menu(current_user.id)
        
        # 获取系统菜单
        system_menus = menu_service.get_system_menus()
        
        # 扁平化菜单
        user_flat_menus = menu_service.flatten_menus(user_menu.menus)
        system_flat_menus = menu_service.flatten_menus(system_menus)
        
        # 统计信息
        stats = {
            "total_user_menus": len(user_flat_menus),
            "total_system_menus": len(system_flat_menus),
            "accessible_percentage": round(len(user_flat_menus) / len(system_flat_menus) * 100, 2) if system_flat_menus else 0,
            "top_level_menus": len(user_menu.menus),
            "has_admin_access": any("admin" in menu.required_roles for menu in user_flat_menus if menu.required_roles)
        }
        
        return BaseResponse(data=stats)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取菜单统计失败: {str(e)}"
        ) 