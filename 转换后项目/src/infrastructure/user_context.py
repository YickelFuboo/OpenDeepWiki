from typing import Optional
from fastapi import Request
from loguru import logger


class UserContext:
    """用户上下文实现"""
    
    def __init__(self, request: Request):
        self.request = request
    
    @property
    def current_user_id(self) -> Optional[str]:
        """获取当前用户ID"""
        try:
            # 从JWT token中获取用户ID
            # 这里需要根据实际的JWT实现来获取
            user = getattr(self.request.state, 'user', None)
            if user:
                return user.get('id')
            return None
        except Exception as e:
            logger.error(f"获取当前用户ID失败: {e}")
            return None
    
    @property
    def current_user_name(self) -> Optional[str]:
        """获取当前用户名"""
        try:
            user = getattr(self.request.state, 'user', None)
            if user:
                return user.get('username')
            return None
        except Exception as e:
            logger.error(f"获取当前用户名失败: {e}")
            return None
    
    @property
    def current_user_email(self) -> Optional[str]:
        """获取当前用户邮箱"""
        try:
            user = getattr(self.request.state, 'user', None)
            if user:
                return user.get('email')
            return None
        except Exception as e:
            logger.error(f"获取当前用户邮箱失败: {e}")
            return None
    
    @property
    def current_user_role(self) -> Optional[str]:
        """获取当前用户角色"""
        try:
            user = getattr(self.request.state, 'user', None)
            if user:
                return user.get('role')
            return None
        except Exception as e:
            logger.error(f"获取当前用户角色失败: {e}")
            return None
    
    @property
    def is_authenticated(self) -> bool:
        """判断用户是否已认证"""
        try:
            user = getattr(self.request.state, 'user', None)
            return user is not None
        except Exception as e:
            logger.error(f"检查用户认证状态失败: {e}")
            return False
    
    @property
    def is_admin(self) -> bool:
        """判断用户是否是管理员"""
        return self.current_user_role == "admin" 