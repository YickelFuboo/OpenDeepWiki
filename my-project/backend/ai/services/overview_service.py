import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from config import get_settings
from models.warehouse import Warehouse
from ..core.kernel_factory import KernelFactory

logger = logging.getLogger(__name__)


class OverviewService:
    """项目概述服务类，负责生成项目的详细概述"""
    
    def __init__(self, db: Session):
        """
        初始化项目概述服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.settings = get_settings()
    
    async def generate_project_overview(
        self, 
        kernel, 
        catalogue: str, 
        git_repository: str, 
        branch: str, 
        readme: str, 
        classify_type: Optional[str] = None
    ) -> str:
        """
        生成项目概述
        
        Args:
            kernel: AI内核
            catalogue: 目录结构
            git_repository: Git仓库地址
            branch: 分支名称
            readme: README内容
            classify_type: 项目分类类型
            
        Returns:
            生成的项目概述
        """
        try:
            # 构建项目概述生成提示词
            prompt_name = "Overview"
            if classify_type:
                prompt_name += classify_type
            
            prompt = f"""
            请根据以下信息生成项目的详细概述：
            
            仓库信息：
            - 地址：{git_repository.replace('.git', '')}
            - 分支：{branch}
            
            README内容：
            {readme}
            
            目录结构：
            {catalogue}
            
            请生成一个详细的项目概述，包含：
            1. 项目背景和目标
            2. 技术栈分析
            3. 核心功能说明
            4. 项目特色和优势
            5. 应用场景和用例
            6. 技术架构分析
            7. 开发团队和社区
            8. 未来发展方向
            
            请使用中文生成，内容要详细且专业。
            """
            
            # 调用AI模型生成项目概述
            result = await self._invoke_ai_model(kernel, prompt)
            
            # 清理结果中的标签
            cleaned_result = self._clean_overview_content(result)
            
            return cleaned_result
            
        except Exception as e:
            logger.error(f"项目概述生成失败: {e}")
            return f"项目概述生成失败: {str(e)}"
    
    def _clean_overview_content(self, content: str) -> str:
        """
        清理概述内容中的标签
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        try:
            # 删除<blog></blog>标签及其内容
            blog_pattern = r'<blog>.*?</blog>'
            content = re.sub(blog_pattern, '', content, flags=re.DOTALL)
            
            # 删除其他可能的标签
            tag_pattern = r'<[^>]+>'
            content = re.sub(tag_pattern, '', content)
            
            # 清理多余的空白字符
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            logger.error(f"清理概述内容失败: {e}")
            return content
    
    async def _invoke_ai_model(self, kernel, prompt: str) -> str:
        """
        调用AI模型
        
        Args:
            kernel: AI内核
            prompt: 提示词
            
        Returns:
            AI模型响应
        """
        try:
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            
            # 获取聊天完成服务
            chat_service = kernel.get_service(ChatCompletionClientBase)
            
            # 调用AI模型
            messages = [{"role": "user", "content": prompt}]
            response = await chat_service.complete_chat(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            raise 