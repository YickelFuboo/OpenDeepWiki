import re
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings

from src.services.prompt_service import PromptService
from src.koala_warehouse.warehouse_classify import ClassifyType
from src.core.config import settings


class OverviewService:
    """项目概述服务"""
    
    def __init__(self):
        self.prompt_service = PromptService()
    
    async def generate_project_overview(
        self, 
        kernel: Kernel, 
        catalog: str, 
        git_repository: str,
        branch: str, 
        readme: str, 
        classify: Optional[ClassifyType] = None
    ) -> str:
        """生成项目概述"""
        try:
            # 构建提示词名称
            prompt_name = "Overview"
            if classify:
                prompt_name += classify.value
            
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Warehouse", prompt_name)
            if not prompt_template:
                prompt_template = """
                请根据以下信息生成项目概述：
                
                目录结构：{catalogue}
                仓库地址：{git_repository}
                分支名称：{branch}
                README内容：{readme}
                
                请生成详细的项目概述，包括项目介绍、主要功能、技术栈、架构说明等。
                使用Markdown格式输出。
                """
            
            # 构建提示词参数
            prompt_args = {
                "catalogue": catalog,
                "git_repository": git_repository.replace(".git", ""),
                "branch": branch,
                "readme": readme
            }
            
            # 替换提示词中的参数
            prompt = prompt_template.format(**prompt_args)
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                max_tokens=self._get_max_tokens(settings.openai.chat_model)
            )
            
            # 执行提示词
            response = await kernel.invoke(prompt, execution_settings=execution_settings)
            result = str(response)
            
            # 提取<blog></blog>中的内容
            blog_pattern = r'<blog>(.*?)</blog>'
            blog_match = re.search(blog_pattern, result, re.DOTALL)
            
            if blog_match:
                result = blog_match.group(1)
            
            # 提取```markdown中的内容
            markdown_pattern = r'```markdown(.*?)```'
            markdown_match = re.search(markdown_pattern, result, re.DOTALL)
            
            if markdown_match:
                result = markdown_match.group(1)
            
            return result.strip()
            
        except Exception as e:
            print(f"生成项目概述失败: {e}")
            return ""
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096) 