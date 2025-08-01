from typing import Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger


class ResultFilter:
    """结果过滤器"""
    
    @staticmethod
    async def process_response(request: Request, call_next) -> Response:
        """处理响应"""
        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
            
            # 如果响应已经是JSONResponse，直接返回
            if isinstance(response, JSONResponse):
                return response
            
            # 获取响应内容
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # 解析响应内容
            try:
                import json
                data = json.loads(response_body.decode())
            except:
                data = response_body.decode()
            
            # 构建标准响应格式
            result = {
                "code": 200,
                "data": data
            }
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"处理响应失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "内部服务器错误"
                }
            )
    
    @staticmethod
    def create_success_response(data: Any = None) -> dict:
        """创建成功响应"""
        return {
            "code": 200,
            "data": data
        }
    
    @staticmethod
    def create_error_response(code: int, message: str) -> dict:
        """创建错误响应"""
        return {
            "code": code,
            "message": message
        } 