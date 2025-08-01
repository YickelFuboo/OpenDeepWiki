import re
import json
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings
from loguru import logger

from src.services.prompt_service import PromptService
from src.services.kernel_factory import KernelFactory
from src.koala_warehouse.warehouse_classify import ClassifyType
from src.models.warehouse import Warehouse
from src.core.config import settings


@dataclass
class DocumentResultCatalogue:
    """文档结果目录"""
    items: list = field(default_factory=list)
    delete_id: list = field(default_factory=list)


class GenerateThinkCatalogueService:
    """生成思考目录服务"""
    
    def __init__(self):
        self.prompt_service = PromptService()
    
    async def generate_catalogue(
        self, 
        path: str, 
        git_repository: str,
        catalogue: str,
        warehouse: Warehouse, 
        classify: Optional[ClassifyType] = None
    ) -> Optional[DocumentResultCatalogue]:
        """生成目录"""
        try:
            # 构建提示词名称
            prompt_name = "AnalyzeCatalogue"
            if classify:
                prompt_name += classify.value
            
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Warehouse", prompt_name)
            if not prompt_template:
                prompt_template = """
                请分析以下代码文件并生成文档目录结构：
                
                代码文件：{code_files}
                仓库地址：{git_repository_url}
                仓库名称：{repository_name}
                
                请生成详细的文档目录结构，包括每个部分的标题、描述和内容提示。
                使用JSON格式输出。
                """
            
            # 构建提示词参数
            prompt_args = {
                "code_files": catalogue,
                "git_repository_url": git_repository.replace(".git", ""),
                "repository_name": warehouse.name
            }
            
            # 替换提示词中的参数
            prompt = prompt_template.format(**prompt_args)
            
            # 创建分析模型内核
            analysis_model = KernelFactory.get_kernel(
                settings.openai.endpoint,
                settings.openai.chat_api_key,
                path,
                settings.openai.analysis_model,
                False
            )
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                temperature=0.5,
                max_tokens=self._get_max_tokens(settings.openai.analysis_model)
            )
            
            # 构建对话历史
            history = [
                {"role": "system", "content": "你是一个专业的代码分析助手。"},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "Ok. Now I will start analyzing the core file. And I won't ask you questions or notify you. I will directly provide you with the required content. Please confirm"},
                {"role": "user", "content": "OK, I confirm that you can start analyzing the core file now. Please proceed with the analysis and provide the relevant content as required. There is no need to ask questions or notify me. The generated document structure will be refined and a complete and detailed directory structure of document types will be provided through project file reading and analysis."}
            ]
            
            retry_count = 0
            max_retries = 5
            exception = None
            
            while retry_count < max_retries:
                try:
                    # 执行提示词
                    response = await analysis_model.invoke(
                        prompt, 
                        execution_settings=execution_settings
                    )
                    result_str = str(response)
                    
                    # 如果需要优化质量
                    if hasattr(settings, 'refine_and_enhance_quality') and settings.refine_and_enhance_quality:
                        history.append({"role": "assistant", "content": result_str})
                        history.append({
                            "role": "user", 
                            "content": "The directory you have provided now is not detailed enough, and the project code files have not been carefully analyzed. Generate a complete project document directory structure and conduct a detailed analysis Organize hierarchically with clear explanations for each component's role and functionality. Please do your best and spare no effort."
                        })
                        
                        response = await analysis_model.invoke(
                            history[-1]["content"], 
                            execution_settings=execution_settings
                        )
                        result_str = str(response)
                    
                    # 提取JSON内容
                    result_str = self._extract_json_content(result_str)
                    
                    # 解析JSON
                    try:
                        result_data = json.loads(result_str.strip())
                        result = DocumentResultCatalogue(
                            items=result_data.get("items", []),
                            delete_id=result_data.get("delete_id", [])
                        )
                        return result
                    except json.JSONDecodeError as e:
                        logger.error(f"反序列化失败: {e}, 原始字符串: {result_str}")
                        raise
                    
                except Exception as e:
                    logger.warning(f"处理仓库 {path}, 处理标题 {warehouse.name} 失败: {e}")
                    exception = e
                    retry_count += 1
                    
                    if retry_count >= max_retries:
                        logger.error(f"处理 {warehouse.name} 失败，已重试 {retry_count} 次，错误：{e}")
                    else:
                        # 等待一段时间后重试
                        await asyncio.sleep(5 * retry_count)
            
            return None
            
        except Exception as e:
            logger.error(f"生成目录失败: {e}")
            return None
    
    def _extract_json_content(self, content: str) -> str:
        """提取JSON内容"""
        # 尝试提取<documentation_structure>标签中的内容
        doc_pattern = r'<documentation_structure>(.*?)</documentation_structure>'
        doc_match = re.search(doc_pattern, content, re.DOTALL)
        
        if doc_match:
            return doc_match.group(1)
        
        # 尝试提取```json代码块
        json_pattern = r'```json(.*?)```'
        json_match = re.search(json_pattern, content, re.DOTALL)
        
        if json_match:
            return json_match.group(1)
        
        # 尝试提取JSON对象
        json_obj_pattern = r'\{(?:[^{}]|(?<open>{)|(?<-open>}))*(?(open)(?!))\}'
        json_obj_match = re.search(json_obj_pattern, content, re.DOTALL)
        
        if json_obj_match:
            return json_obj_match.group(0)
        
        return content
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096) 