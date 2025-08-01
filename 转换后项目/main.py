import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.core.config import settings
from src.core.database import engine, Base
from src.api import api_router
from src.infrastructure import DocumentsHelper, UserContext, ResultFilter
from src.extensions import SitemapExtensions, DbContextExtensions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时执行
    logger.info("应用程序启动中...")
    
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库表创建完成")
    yield
    
    # 关闭时执行
    logger.info("应用程序关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="KoalaWiki Python Backend",
    description="KoalaWiki Python后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加结果过滤器中间件
@app.middleware("http")
async def result_filter_middleware(request: Request, call_next):
    """结果过滤器中间件"""
    return await ResultFilter.process_response(request, call_next)

# 添加用户上下文中间件
@app.middleware("http")
async def user_context_middleware(request: Request, call_next):
    """用户上下文中间件"""
    # 这里可以添加用户上下文处理逻辑
    response = await call_next(request)
    return response

# 配置数据库上下文
DbContextExtensions.add_db_context(app)

# 映射站点地图
SitemapExtensions.map_sitemap(app)

# 包含API路由
app.include_router(api_router, prefix="/api")

# 挂载静态文件
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "KoalaWiki Python Backend",
        "version": "1.0.0",
        "status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 