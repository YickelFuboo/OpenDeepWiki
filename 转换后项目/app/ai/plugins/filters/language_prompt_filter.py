"""
语言提示过滤器
将C#的LanguagePromptFilter转换为Python版本
"""

from typing import Callable, Any
from abc import ABC, abstractmethod


class PromptRenderContext:
    """提示渲染上下文"""
    
    def __init__(self, rendered_prompt: str = ""):
        self.rendered_prompt = rendered_prompt


class IPromptRenderFilter(ABC):
    """提示渲染过滤器接口"""
    
    @abstractmethod
    async def on_prompt_render_async(
        self, 
        context: PromptRenderContext, 
        next_func: Callable[[PromptRenderContext], Any]
    ):
        """处理提示渲染"""
        pass


class LanguagePromptFilter(IPromptRenderFilter):
    """语言提示过滤器"""
    
    async def on_prompt_render_async(
        self, 
        context: PromptRenderContext, 
        next_func: Callable[[PromptRenderContext], Any]
    ):
        """处理提示渲染，添加语言相关前缀"""
        await next_func(context)
        
        # 添加语言前缀，类似于C#版本
        context.rendered_prompt = "/no_think " + context.rendered_prompt + "\n" + "Language: Chinese" 