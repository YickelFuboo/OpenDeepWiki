from fastapi import Depends, HTTPException, status
from typing import Optional

# 简化的用户上下文
class SimpleUserContext:
    def __init__(self, user_id: str = "default", username: str = "default", email: str = "default@example.com", role: str = "user"):
        self.current_user_id = user_id
        self.id = user_id  # 兼容性
        self.username = username
        self.email = email
        self.role = role
        self.is_admin = role == "admin"

# 简化的认证装饰器
def require_user():
    """简化的用户认证装饰器"""
    def decorator(func):
        return func
    return decorator

def require_admin():
    """简化的管理员认证装饰器"""
    def decorator(func):
        return func
    return decorator

def get_current_user():
    """获取当前用户（简化版）"""
    def get_user():
        return SimpleUserContext()
    return Depends(get_user)

def get_current_active_user():
    """获取当前活跃用户（简化版）"""
    def get_user():
        return SimpleUserContext()
    return Depends(get_user) 