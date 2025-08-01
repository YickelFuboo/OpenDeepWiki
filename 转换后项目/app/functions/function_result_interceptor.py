from typing import Callable, Any
from semantic_kernel import KernelFunction


class FunctionResultInterceptor:
    """函数结果拦截器"""
    
    async def on_function_invocation_async(
        self,
        context: Any,
        next_func: Callable[[Any], Any]
    ):
        """
        函数调用拦截器
        
        Args:
            context: 函数调用上下文
            next_func: 下一个处理函数
        """
        try:
            # 在函数调用前可以添加日志、验证等逻辑
            # 例如：logger.info(f"调用函数: {context.function_name}")
            
            # 执行函数
            result = await next_func(context)
            
            # 在函数调用后可以添加结果处理、日志等逻辑
            # 例如：logger.info(f"函数执行完成: {context.function_name}")
            
            return result
            
        except Exception as e:
            # 处理异常
            # logger.error(f"函数执行失败: {context.function_name}, 错误: {e}")
            raise 