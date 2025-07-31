"""
OAuth第三方登录API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db.database.factory import get_db
from ..service.auth_mgmt.oauth_service import OAuthService
from ..api.schemes.user import OAuthLogin, OAuthBind, OIDCLogin
from ..logger.logger import logger

router = APIRouter()

@router.get("/{provider}/authorize")
async def oauth_authorize(provider: str, request: Request, db: Session = Depends(get_db)):
    """
    获取OAuth授权URL
    
    Args:
        provider: 提供商 (github, google, wechat, alipay, oidc)
        request: 请求对象
        db: 数据库会话
    
    Returns:
        重定向到OAuth授权页面
    """
    try:
        oauth_service = OAuthService(db)
        oauth_provider = oauth_service.get_oauth_provider(provider)
        
        if not oauth_provider:
            raise HTTPException(status_code=404, detail=f"未找到{provider}提供商配置")
        
        # 生成state参数
        state = oauth_service.generate_state_parameter()
        
        # 构建授权URL
        auth_url = oauth_provider.auth_url
        params = {
            "client_id": oauth_provider.client_id,
            "redirect_uri": oauth_provider.redirect_uri,
            "response_type": "code",
            "state": state
        }
        
        # 添加scope参数
        if provider == "github":
            params["scope"] = "read:user user:email"
        elif provider == "google":
            params["scope"] = "openid email profile"
        elif provider == "wechat":
            params["scope"] = "snsapi_login"
        elif provider == "alipay":
            params["scope"] = "auth_user"
        elif provider == "oidc":
            params["scope"] = "openid email profile"
        
        # 构建完整URL
        from urllib.parse import urlencode
        full_url = f"{auth_url}?{urlencode(params)}"
        
        # 在实际应用中，应该将state存储到session或缓存中
        # 这里简化处理，直接返回重定向
        return RedirectResponse(url=full_url)
        
    except Exception as e:
        logger.error(f"获取{provider}授权URL失败: {e}")
        raise HTTPException(status_code=500, detail="获取授权URL失败")

@router.post("/{provider}/callback")
async def oauth_callback(
    provider: str,
    oauth_data: OAuthLogin,
    db: Session = Depends(get_db)
):
    """
    OAuth回调处理
    
    Args:
        provider: 提供商
        oauth_data: OAuth数据
        db: 数据库会话
    
    Returns:
        登录结果
    """
    try:
        oauth_service = OAuthService(db)
        result = oauth_service.handle_oauth_login(
            provider=provider,
            code=oauth_data.code,
            state=oauth_data.state
        )
        
        return {
            "message": f"{provider}登录成功",
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": result["user"]
        }
        
    except Exception as e:
        logger.error(f"{provider}登录失败: {e}")
        raise HTTPException(status_code=400, detail=f"{provider}登录失败")

@router.post("/{provider}/bind")
async def bind_oauth_account(
    provider: str,
    oauth_bind: OAuthBind,
    db: Session = Depends(get_db)
):
    """
    绑定OAuth账号
    
    Args:
        provider: 提供商
        oauth_bind: 绑定数据
        db: 数据库会话
    
    Returns:
        绑定结果
    """
    try:
        oauth_service = OAuthService(db)
        
        # 获取OAuth用户信息
        user_info = await oauth_service.get_user_info(provider, oauth_bind.access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="获取OAuth用户信息失败")
        
        # 绑定账号
        success = oauth_service.bind_oauth_account(
            user_id=oauth_bind.user_id,
            provider=provider,
            oauth_user_info=user_info
        )
        
        if success:
            return {"message": f"绑定{provider}账号成功"}
        else:
            raise HTTPException(status_code=400, detail=f"绑定{provider}账号失败")
            
    except Exception as e:
        logger.error(f"绑定{provider}账号失败: {e}")
        raise HTTPException(status_code=500, detail=f"绑定{provider}账号失败")

@router.delete("/{provider}/unbind")
async def unbind_oauth_account(
    provider: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    解绑OAuth账号
    
    Args:
        provider: 提供商
        user_id: 用户ID
        db: 数据库会话
    
    Returns:
        解绑结果
    """
    try:
        oauth_service = OAuthService(db)
        success = oauth_service.unbind_oauth_account(user_id, provider)
        
        if success:
            return {"message": f"解绑{provider}账号成功"}
        else:
            raise HTTPException(status_code=400, detail=f"解绑{provider}账号失败")
            
    except Exception as e:
        logger.error(f"解绑{provider}账号失败: {e}")
        raise HTTPException(status_code=500, detail=f"解绑{provider}账号失败")

@router.get("/providers")
async def get_oauth_providers(db: Session = Depends(get_db)):
    """
    获取可用的OAuth提供商列表
    
    Args:
        db: 数据库会话
    
    Returns:
        提供商列表
    """
    try:
        from ..db.database.models.user import OAuthProvider
        providers = db.query(OAuthProvider).filter(OAuthProvider.is_active == True).all()
        
        return {
            "providers": [
                {
                    "provider": p.provider,
                    "name": p.provider.title(),
                    "auth_url": p.auth_url
                }
                for p in providers
            ]
        }
        
    except Exception as e:
        logger.error(f"获取OAuth提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取提供商列表失败") 

@router.post("/oidc/callback")
async def oidc_callback(
    oidc_data: OIDCLogin,
    db: Session = Depends(get_db)
):
    """
    OIDC回调处理
    
    Args:
        oidc_data: OIDC数据
        db: 数据库会话
    
    Returns:
        登录结果
    """
    try:
        oauth_service = OAuthService(db)
        result = oauth_service.handle_oidc_login(
            issuer=oidc_data.issuer,
            code=oidc_data.code,
            state=oidc_data.state
        )
        
        return {
            "message": "OIDC登录成功",
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": result["user"]
        }
        
    except Exception as e:
        logger.error(f"OIDC登录失败: {e}")
        raise HTTPException(status_code=400, detail="OIDC登录失败")

@router.get("/oidc/discover/{issuer:path}")
async def oidc_discover(issuer: str, db: Session = Depends(get_db)):
    """
    发现OIDC配置
    
    Args:
        issuer: OIDC发行者URL
        db: 数据库会话
    
    Returns:
        OIDC配置信息
    """
    try:
        oauth_service = OAuthService(db)
        config = oauth_service.discover_oidc_config(issuer)
        
        if config:
            return {
                "issuer": issuer,
                "config": config
            }
        else:
            raise HTTPException(status_code=404, detail="无法发现OIDC配置")
            
    except Exception as e:
        logger.error(f"OIDC配置发现失败: {e}")
        raise HTTPException(status_code=500, detail="OIDC配置发现失败") 