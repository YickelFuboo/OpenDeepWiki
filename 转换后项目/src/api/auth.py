from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.dto.auth_dto import LoginDto, RegisterDto, TokenDto, RefreshTokenDto
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.dto.user_dto import UserInfoDto

auth_router = APIRouter()


@auth_router.post("/login", response_model=TokenDto)
async def login(
    login_dto: LoginDto,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    auth_service = AuthService(db)
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 执行登录
    token_dto = await auth_service.login(login_dto, client_ip)
    if not token_dto:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 设置Cookie
    response = JSONResponse(content=token_dto.dict())
    response.set_cookie(
        key="token",
        value=token_dto.access_token,
        httponly=True,
        max_age=24 * 60 * 60,  # 24小时
        samesite="lax"
    )
    
    return response


@auth_router.post("/register", response_model=UserInfoDto)
async def register(
    register_dto: RegisterDto,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.register(register_dto)
        user_service = UserService(db)
        return user_service.user_to_dto(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@auth_router.post("/refresh", response_model=TokenDto)
async def refresh_token(
    refresh_dto: RefreshTokenDto,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    auth_service = AuthService(db)
    
    token_dto = await auth_service.refresh_token(refresh_dto.refresh_token)
    if not token_dto:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    return token_dto


@auth_router.post("/logout")
async def logout():
    """用户登出"""
    response = JSONResponse(content={"message": "登出成功"})
    response.delete_cookie(key="token")
    return response 