from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
import time
import traceback


class GlobalMiddleware:
    """全局中间件"""
    
    @staticmethod
    async def handle_request(request: Request, call_next):
        """处理请求的全局中间件"""
        start_time = time.time()
        
        try:
            # 记录请求开始
            logger.info(f"开始处理请求: {request.method} {request.url.path}")
            
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(f"请求处理完成: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            logger.error(f"请求处理失败: {request.method} {request.url.path} - {str(e)}")
            logger.error(traceback.format_exc())
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "内部服务器错误",
                    "message": str(e),
                    "path": request.url.path,
                    "method": request.method
                }
            )
    
    @staticmethod
    async def handle_cors(request: Request, call_next):
        """处理CORS的中间件"""
        response = await call_next(request)
        
        # 添加CORS头
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
    
    @staticmethod
    async def handle_logging(request: Request, call_next):
        """处理日志记录的中间件"""
        # 记录请求信息
        logger.info(f"收到请求: {request.method} {request.url.path}")
        logger.info(f"请求头: {dict(request.headers)}")
        
        response = await call_next(request)
        
        # 记录响应信息
        logger.info(f"响应状态: {response.status_code}")
        
        return response
    
    @staticmethod
    async def handle_error_handling(request: Request, call_next):
        """处理错误处理的中间件"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"未处理的异常: {str(e)}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "服务器内部错误",
                    "message": "发生了未预期的错误"
                }
            )


def setup_global_middleware(app):
    """设置全局中间件"""
    from fastapi import FastAPI
    
    # 添加全局中间件
    app.middleware("http")(GlobalMiddleware.handle_request)
    app.middleware("http")(GlobalMiddleware.handle_cors)
    app.middleware("http")(GlobalMiddleware.handle_logging)
    app.middleware("http")(GlobalMiddleware.handle_error_handling)
    
    logger.info("全局中间件设置完成") 