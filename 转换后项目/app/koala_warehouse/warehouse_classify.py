import re
import json
from typing import Optional
from enum import Enum
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings

from src.services.prompt_service import PromptService
from src.conf.settings import settings


class ClassifyType(str, Enum):
    """仓库分类类型"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    LIBRARY = "library"
    TOOL = "tool"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class WarehouseClassify:
    """仓库分类服务"""
    
    def __init__(self):
        self.prompt_service = PromptService()
    
    async def classify_async(self, kernel: Kernel, catalog: str, readme: str) -> Optional[ClassifyType]:
        """根据仓库信息分析得出仓库分类"""
        try:
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Warehouse", "RepositoryClassification")
            if not prompt_template:
                prompt_template = """
                请分析以下仓库信息并给出分类：
                
                目录结构：{catalog}
                README内容：{readme}
                
                请返回JSON格式的分类结果，格式如下：
                <classify>classifyName:分类名称</classify>
                
                可选分类：frontend, backend, fullstack, mobile, desktop, library, tool, documentation, other
                """
            
            # 构建提示词参数
            prompt_args = {
                "category": catalog,
                "readme": readme
            }
            
            # 替换提示词中的参数
            prompt = prompt_template.format(**prompt_args)
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                temperature=0.1,
                max_tokens=self._get_max_tokens(settings.openai.chat_model)
            )
            
            # 执行提示词
            result = ""
            is_deep = False
            
            # 这里简化实现，实际应该使用streaming
            response = await kernel.invoke(prompt, execution_settings=execution_settings)
            result = str(response)
            
            # 提取分类结果
            classify_pattern = r'<classify>(.*?)</classify>'
            match = re.search(classify_pattern, result, re.DOTALL)
            
            if match:
                extracted_content = match.group(1).replace("classifyName:", "").strip()
                
                # 尝试解析为枚举类型
                try:
                    classify_type = ClassifyType(extracted_content.lower())
                    return classify_type
                except ValueError:
                    # 如果无法解析，尝试模糊匹配
                    return self._fuzzy_match_classify(extracted_content)
            
            return None
            
        except Exception as e:
            print(f"仓库分类失败: {e}")
            return None
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096)
    
    def _fuzzy_match_classify(self, content: str) -> Optional[ClassifyType]:
        """模糊匹配分类"""
        content_lower = content.lower()
        
        # 关键词匹配
        if any(keyword in content_lower for keyword in ["frontend", "react", "vue", "angular", "ui", "界面"]):
            return ClassifyType.FRONTEND
        elif any(keyword in content_lower for keyword in ["backend", "api", "server", "服务端"]):
            return ClassifyType.BACKEND
        elif any(keyword in content_lower for keyword in ["fullstack", "全栈", "前后端"]):
            return ClassifyType.FULLSTACK
        elif any(keyword in content_lower for keyword in ["mobile", "android", "ios", "移动端"]):
            return ClassifyType.MOBILE
        elif any(keyword in content_lower for keyword in ["desktop", "桌面", "客户端"]):
            return ClassifyType.DESKTOP
        elif any(keyword in content_lower for keyword in ["library", "库", "框架"]):
            return ClassifyType.LIBRARY
        elif any(keyword in content_lower for keyword in ["tool", "工具", "utility"]):
            return ClassifyType.TOOL
        elif any(keyword in content_lower for keyword in ["documentation", "文档", "docs"]):
            return ClassifyType.DOCUMENTATION
        else:
            return ClassifyType.OTHER 