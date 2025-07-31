from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from models.user import User, UserInRole, Role
from schemas.user import LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from utils.auth import create_access_token, create_refresh_token, verify_token
from utils.password import verify_password
from config import JWTConfig


class AuthService:
    """认证服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        # 查找用户（支持用户名或邮箱登录）
        user = self.db.query(User).filter(
            (User.name == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return user
    
    def login(self, login_data: LoginRequest, client_ip: str = None) -> LoginResponse:
        """用户登录"""
        user = self.authenticate_user(login_data.username, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        self.db.commit()
        
        # 获取用户角色
        user_roles = self.db.query(UserInRole).filter(UserInRole.user_id == user.id).all()
        role_ids = [ur.role_id for ur in user_roles]
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
        role_names = [role.name for role in roles]
        
        # 创建令牌
        token_data = {"sub": user.id, "username": user.name, "roles": role_names}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # 构建用户响应
        from schemas.user import UserResponse
        user_response = UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar=user.avatar,
            last_login_at=user.last_login_at,
            last_login_ip=user.last_login_ip,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=role_names
        )
        
        return LoginResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_response,
            message="登录成功"
        )
    
    def refresh_token(self, refresh_data: RefreshTokenRequest) -> RefreshTokenResponse:
        """刷新令牌"""
        try:
            payload = verify_token(refresh_data.refresh_token)
            user_id = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
            
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在或已被禁用"
                )
            
            # 获取用户角色
            user_roles = self.db.query(UserInRole).filter(UserInRole.user_id == user.id).all()
            role_ids = [ur.role_id for ur in user_roles]
            roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
            role_names = [role.name for role in roles]
            
            # 创建新令牌
            token_data = {"sub": user.id, "username": user.name, "roles": role_names}
            new_access_token = create_access_token(token_data)
            new_refresh_token = create_refresh_token(token_data)
            
            return RefreshTokenResponse(
                success=True,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                message="令牌刷新成功"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌失败"
            )
    
    def register(self, username: str, email: str, password: str) -> LoginResponse:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(
            (User.name == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        # 创建新用户
        from utils.password import hash_password
        user = User(
            id=str(uuid.uuid4()),
            name=username,
            email=email,
            password=hash_password(password),
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # 分配默认用户角色
        default_role = self.db.query(Role).filter(Role.name == "user").first()
        if default_role:
            user_role = UserInRole(
                id=str(uuid.uuid4()),
                user_id=user.id,
                role_id=default_role.id
            )
            self.db.add(user_role)
            self.db.commit()
        
        # 返回登录响应
        from schemas.user import LoginRequest
        login_data = LoginRequest(username=username, password=password)
        return self.login(login_data)
    
    def logout(self, user: User) -> dict:
        """用户登出"""
        # 在实际应用中，可以将令牌加入黑名单
        # 这里简单返回成功消息
        return {"success": True, "message": "登出成功"} 