"""
User-Service 主入口文件
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from db.database.factory import init_database, get_db, close_db
from db.storage.factory import init_storage, close_storage, get_storage
from api import users, auth, roles, avatar
from logger.logger import logger

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="用户认证与权限管理微服务",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    try:
        # 懒加载初始化 - 在第一次使用时自动初始化
        logger.info(f"{settings.app_name} v{settings.app_version} 启动成功")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    logger.info("应用正在关闭...")
    close_storage()
    close_db()

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接 - 会触发懒加载初始化
        db = get_db()
        db.close()
        
        # 检查存储连接 - 会触发懒加载初始化
        storage = get_storage()
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "connected",
            "storage": "connected"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="服务不健康")

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证管理"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["角色管理"])
app.include_router(avatar.router, prefix="/api/v1/avatar", tags=["头像管理"])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 