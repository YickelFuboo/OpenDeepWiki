"""
OAuth第三方登录服务
"""

import httpx
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.sql import func

from ...db.database.models.user import User, OAuthProvider
from ...db.database.factory import get_db
from ...service.auth_mgmt.auth_service import AuthService
from ...logger.logger import logger


class OAuthService:
    """OAuth服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)
        self._init_oauth_providers()
    
    def _init_oauth_providers(self):
        """初始化OAuth提供商配置"""
        from ...config.settings import get_settings
        settings = get_settings()
        
        providers = [
            {
                "provider": "github",
                "client_id": settings.oauth.github_client_id,
                "client_secret": settings.oauth.github_client_secret,
                "redirect_uri": settings.oauth.github_redirect_uri,
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user"
            },
            {
                "provider": "google",
                "client_id": settings.oauth.google_client_id,
                "client_secret": settings.oauth.google_client_secret,
                "redirect_uri": settings.oauth.google_redirect_uri,
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
            },
            {
                "provider": "wechat",
                "client_id": settings.oauth.wechat_app_id,
                "client_secret": settings.oauth.wechat_app_secret,
                "redirect_uri": settings.oauth.wechat_redirect_uri,
                "auth_url": "https://open.weixin.qq.com/connect/qrconnect",
                "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
                "user_info_url": "https://api.weixin.qq.com/sns/userinfo"
            },
            {
                "provider": "alipay",
                "client_id": settings.oauth.alipay_app_id,
                "client_secret": settings.oauth.alipay_private_key,
                "redirect_uri": settings.oauth.alipay_redirect_uri,
                "auth_url": "https://openauth.alipay.com/oauth2/publicAppAuthorize.htm",
                "token_url": "https://openapi.alipay.com/gateway.do",
                "user_info_url": "https://openapi.alipay.com/gateway.do"
            },
            {
                "provider": "oidc",
                "client_id": settings.oauth.oidc_client_id,
                "client_secret": settings.oauth.oidc_client_secret,
                "redirect_uri": settings.oauth.oidc_redirect_uri,
                "auth_url": f"{settings.oauth.oidc_issuer}/oauth/authorize",
                "token_url": f"{settings.oauth.oidc_issuer}/oauth/token",
                "user_info_url": f"{settings.oauth.oidc_issuer}/userinfo"
            }
        ]
        
        for provider_config in providers:
            if provider_config["client_id"] and provider_config["client_secret"]:
                self._ensure_oauth_provider(provider_config)
    
    def _ensure_oauth_provider(self, config: Dict[str, str]):
        """确保OAuth提供商配置存在"""
        existing = self.db.query(OAuthProvider).filter(
            OAuthProvider.provider == config["provider"]
        ).first()
        
        if not existing:
            oauth_provider = OAuthProvider(
                provider=config["provider"],
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                redirect_uri=config["redirect_uri"],
                auth_url=config["auth_url"],
                token_url=config["token_url"],
                user_info_url=config["user_info_url"],
                is_active=True
            )
            self.db.add(oauth_provider)
            self.db.commit()
            logger.info(f"初始化OAuth提供商配置: {config['provider']}")
        elif not existing.is_active:
            existing.is_active = True
            self.db.commit()
            logger.info(f"激活OAuth提供商配置: {config['provider']}")
    
    def get_oauth_provider(self, provider: str) -> Optional[OAuthProvider]:
        """获取OAuth提供商配置"""
        return self.db.query(OAuthProvider).filter(
            and_(
                OAuthProvider.provider == provider,
                OAuthProvider.is_active == True
            )
        ).first()
    
    def discover_oidc_config(self, issuer: str) -> Optional[Dict[str, Any]]:
        """OIDC配置发现"""
        try:
            with httpx.Client() as client:
                response = client.get(f"{issuer}/.well-known/openid-configuration")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"OIDC配置发现失败: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"OIDC配置发现异常: {e}")
            return None
    
    def validate_state_parameter(self, state: str, expected_state: str) -> bool:
        """验证state参数"""
        return state == expected_state
    
    def generate_state_parameter(self) -> str:
        """生成state参数"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def generate_pkce_challenge(self) -> tuple[str, str]:
        """生成PKCE挑战码"""
        import secrets
        import hashlib
        import base64
        
        # 生成随机码验证器
        code_verifier = secrets.token_urlsafe(32)
        
        # 生成挑战码
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return code_verifier, code_challenge
    
    def validate_pkce_verifier(self, code_verifier: str, code_challenge: str) -> bool:
        """验证PKCE验证器"""
        import hashlib
        import base64
        
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        return expected_challenge == code_challenge
    
    def get_github_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取GitHub用户信息"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            with httpx.Client() as client:
                response = client.get(
                    "https://api.github.com/user",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取GitHub用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取GitHub用户信息异常: {e}")
            return None
    
    def get_google_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取Google用户信息"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            with httpx.Client() as client:
                response = client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取Google用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取Google用户信息异常: {e}")
            return None
    
    def get_wechat_user_info(self, access_token: str, openid: str) -> Optional[Dict[str, Any]]:
        """获取微信用户信息"""
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://api.weixin.qq.com/sns/userinfo",
                    params={
                        "access_token": access_token,
                        "openid": openid,
                        "lang": "zh_CN"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("errcode") == 0:
                        return data
                    else:
                        logger.error(f"获取微信用户信息失败: {data}")
                        return None
                else:
                    logger.error(f"获取微信用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取微信用户信息异常: {e}")
            return None
    
    def get_alipay_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取支付宝用户信息"""
        try:
            # 支付宝用户信息获取需要特殊的签名处理
            # 这里简化处理，实际需要按照支付宝API规范
            with httpx.Client() as client:
                response = client.get(
                    "https://openapi.alipay.com/gateway.do",
                    params={
                        "method": "alipay.user.info.share",
                        "app_id": "your_app_id",
                        "format": "json",
                        "charset": "utf-8",
                        "sign_type": "RSA2",
                        "timestamp": "2023-01-01 00:00:00",
                        "version": "1.0",
                        "auth_token": access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取支付宝用户信息失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取支付宝用户信息异常: {e}")
            return None
    
    def create_or_update_user_from_oauth(self, provider: str, oauth_user_info: Dict[str, Any]) -> User:
        """从OAuth用户信息创建或更新用户"""
        try:
            # 根据提供商获取用户ID
            provider_id_field = f"{provider}_id"
            oauth_id = oauth_user_info.get("id") or oauth_user_info.get("openid")
            
            if not oauth_id:
                raise ValueError(f"无法获取{provider}用户ID")
            
            # 查找现有用户
            user = self.db.query(User).filter(
                getattr(User, provider_id_field) == oauth_id
            ).first()
            
            if user:
                # 更新现有用户信息
                user.full_name = oauth_user_info.get("name") or oauth_user_info.get("login")
                user.avatar = oauth_user_info.get("avatar_url")
                user.last_login = func.now()
                self.db.commit()
                logger.info(f"更新{provider}用户: {user.username}")
            else:
                # 创建新用户
                username = oauth_user_info.get("login") or oauth_user_info.get("name") or f"{provider}_{oauth_id}"
                email = oauth_user_info.get("email")
                
                # 确保用户名唯一
                base_username = username
                counter = 1
                while self.db.query(User).filter(User.username == username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    full_name=oauth_user_info.get("name") or oauth_user_info.get("login"),
                    avatar=oauth_user_info.get("avatar_url"),
                    registration_method=provider,
                    **{provider_id_field: oauth_id}
                )
                
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"创建{provider}用户: {user.username}")
            
            return user
            
        except Exception as e:
            logger.error(f"创建或更新{provider}用户失败: {e}")
            raise
    
    def handle_oauth_login(self, provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """处理OAuth登录"""
        try:
            # 获取OAuth提供商配置
            oauth_provider = self.get_oauth_provider(provider)
            if not oauth_provider:
                raise ValueError(f"未找到{provider}提供商配置")
            
            # 获取访问令牌
            access_token = self.get_access_token(provider, code, oauth_provider)
            if not access_token:
                raise ValueError(f"获取{provider}访问令牌失败")
            
            # 获取用户信息
            user_info = self.get_user_info(provider, access_token)
            if not user_info:
                raise ValueError(f"获取{provider}用户信息失败")
            
            # 创建或更新用户
            user = self.create_or_update_user_from_oauth(provider, user_info)
            
            # 生成JWT令牌
            access_token_jwt = self.auth_service.create_access_token(user.id)
            refresh_token_jwt = self.auth_service.create_refresh_token(user.id)
            
            return {
                "access_token": access_token_jwt,
                "refresh_token": refresh_token_jwt,
                "user": user,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"处理{provider}登录失败: {e}")
            raise
    
    def get_access_token(self, provider: str, code: str, oauth_provider: OAuthProvider) -> Optional[str]:
        """获取访问令牌"""
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                data = {
                    "client_id": oauth_provider.client_id,
                    "client_secret": oauth_provider.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": oauth_provider.redirect_uri
                }
                
                with httpx.Client() as client:
                    response = client.post(oauth_provider.token_url, data=data, timeout=10)
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        return token_data.get("access_token")
                    else:
                        logger.error(f"获取{provider}访问令牌失败: {response.status_code} - {response.text}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        return None
                        
            except Exception as e:
                logger.error(f"获取{provider}访问令牌异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
        
        return None
    
    def get_user_info(self, provider: str, access_token: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if provider == "github":
            return self.get_github_user_info(access_token)
        elif provider == "google":
            return self.get_google_user_info(access_token)
        elif provider == "wechat":
            # 微信需要openid，这里简化处理
            return self.get_wechat_user_info(access_token, "openid")
        elif provider == "alipay":
            return self.get_alipay_user_info(access_token)
        elif provider == "oidc":
            return self.get_oidc_user_info(access_token)
        else:
            raise ValueError(f"不支持的OAuth提供商: {provider}")
    
    def get_oidc_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取OIDC用户信息"""
        try:
            # OIDC通常返回JWT格式的ID令牌
            import jwt
            from ...config.settings import get_settings
            
            settings = get_settings()
            
            # 解码JWT令牌（不验证签名，仅获取信息）
            try:
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                return {
                    "id": decoded.get("sub"),
                    "email": decoded.get("email"),
                    "username": decoded.get("preferred_username") or decoded.get("name"),
                    "full_name": decoded.get("name"),
                    "avatar": decoded.get("picture")
                }
            except jwt.InvalidTokenError:
                # 如果不是JWT，尝试作为普通OAuth令牌使用
                with httpx.Client() as client:
                    response = client.get(
                        "https://your-oidc-provider.com/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.error(f"获取OIDC用户信息失败: {response.status_code}")
                        return None
                        
        except Exception as e:
            logger.error(f"获取OIDC用户信息异常: {e}")
            return None
    
    def handle_oidc_login(self, issuer: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """处理OIDC登录"""
        try:
            # 发现OIDC配置
            oidc_config = self.discover_oidc_config(issuer)
            if not oidc_config:
                raise ValueError(f"无法发现OIDC配置: {issuer}")
            
            # 获取访问令牌和ID令牌
            token_response = self.get_oidc_tokens(issuer, code, oidc_config)
            if not token_response:
                raise ValueError("获取OIDC令牌失败")
            
            access_token = token_response.get("access_token")
            id_token = token_response.get("id_token")
            
            # 从ID令牌获取用户信息
            user_info = self.get_oidc_user_info(id_token)
            if not user_info:
                raise ValueError("获取OIDC用户信息失败")
            
            # 创建或更新用户
            user = self.create_or_update_user_from_oauth("oidc", user_info)
            
            # 生成JWT令牌
            access_token_jwt = self.auth_service.create_access_token(user.id)
            refresh_token_jwt = self.auth_service.create_refresh_token(user.id)
            
            return {
                "access_token": access_token_jwt,
                "refresh_token": refresh_token_jwt,
                "user": user,
                "provider": "oidc"
            }
            
        except Exception as e:
            logger.error(f"处理OIDC登录失败: {e}")
            raise
    
    def get_oidc_tokens(self, issuer: str, code: str, oidc_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取OIDC令牌"""
        try:
            from ...config.settings import get_settings
            settings = get_settings()
            
            data = {
                "client_id": settings.oauth.oidc_client_id,
                "client_secret": settings.oauth.oidc_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.oauth.oidc_redirect_uri
            }
            
            with httpx.Client() as client:
                response = client.post(oidc_config["token_endpoint"], data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取OIDC令牌失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取OIDC令牌异常: {e}")
            return None
    
    def bind_oauth_account(self, user_id: str, provider: str, oauth_user_info: Dict[str, Any]) -> bool:
        """绑定OAuth账号"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            provider_id_field = f"{provider}_id"
            oauth_id = oauth_user_info.get("id") or oauth_user_info.get("openid")
            
            if not oauth_id:
                return False
            
            # 检查是否已被其他用户绑定
            existing_user = self.db.query(User).filter(
                getattr(User, provider_id_field) == oauth_id
            ).first()
            
            if existing_user and existing_user.id != user_id:
                return False
            
            # 绑定账号
            setattr(user, provider_id_field, oauth_id)
            self.db.commit()
            
            logger.info(f"用户{user.username}绑定{provider}账号成功")
            return True
            
        except Exception as e:
            logger.error(f"绑定{provider}账号失败: {e}")
            return False
    
    def unbind_oauth_account(self, user_id: str, provider: str) -> bool:
        """解绑OAuth账号"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            provider_id_field = f"{provider}_id"
            setattr(user, provider_id_field, None)
            self.db.commit()
            
            logger.info(f"用户{user.username}解绑{provider}账号成功")
            return True
            
        except Exception as e:
            logger.error(f"解绑{provider}账号失败: {e}")
            return False 