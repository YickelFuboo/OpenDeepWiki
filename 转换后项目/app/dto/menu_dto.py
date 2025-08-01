from typing import List, Optional
from pydantic import BaseModel


class MenuItemDto(BaseModel):
    """菜单项DTO"""
    id: str
    name: str
    path: str
    icon: Optional[str] = None
    order: int = 0
    is_hidden: bool = False
    required_roles: List[str] = []
    children: List["MenuItemDto"] = []


class UserMenuDto(BaseModel):
    """用户菜单DTO"""
    user: Optional["UserInfoDto"] = None
    menus: List[MenuItemDto] = []


# 前向引用
from src.dto.user_dto import UserInfoDto 