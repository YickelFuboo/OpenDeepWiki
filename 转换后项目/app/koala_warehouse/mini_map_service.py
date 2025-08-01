import re
from typing import List, Optional
from dataclasses import dataclass, field
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings

from src.services.prompt_service import PromptService
from src.services.kernel_factory import KernelFactory
from src.models.warehouse import Warehouse
from src.conf.settings import settings


@dataclass
class MiniMapResult:
    """迷你地图结果"""
    title: Optional[str] = None
    url: Optional[str] = None
    nodes: List['MiniMapResult'] = field(default_factory=list)


class MiniMapService:
    """迷你地图服务"""
    
    def __init__(self):
        self.prompt_service = PromptService()
    
    async def generate_mini_map(self, catalogue: str, warehouse: Warehouse, path: str) -> MiniMapResult:
        """生成知识图谱"""
        try:
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Warehouse", "GenerateMindMap")
            if not prompt_template:
                prompt_template = """
                请根据以下代码文件生成知识图谱：
                
                代码文件：{code_files}
                仓库地址：{repository_url}
                分支名称：{branch_name}
                
                请生成结构化的知识图谱，使用Markdown格式，包含标题层级和文件链接。
                格式示例：
                # 主要模块
                ## 核心功能:src/core/main.py
                ### 配置管理:src/core/config.py
                ## 数据模型:src/models/
                ### 用户模型:src/models/user.py
                """
            
            # 构建提示词参数
            prompt_args = {
                "code_files": catalogue,
                "repository_url": warehouse.address.replace(".git", ""),
                "branch_name": warehouse.branch
            }
            
            # 替换提示词中的参数
            prompt = prompt_template.format(**prompt_args)
            
            # 创建内核
            kernel = KernelFactory.get_kernel(
                settings.openai.endpoint,
                settings.openai.chat_api_key,
                path,
                settings.openai.chat_model
            )
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                max_tokens=self._get_max_tokens(settings.openai.chat_model)
            )
            
            # 执行提示词
            response = await kernel.invoke(prompt, execution_settings=execution_settings)
            mini_map_content = str(response)
            
            # 删除thinking标签
            thinking_pattern = r'<thinking>.*?</thinking>'
            mini_map_content = re.sub(thinking_pattern, '', mini_map_content, flags=re.DOTALL).strip()
            
            # 解析知识图谱
            lines = [line.strip() for line in mini_map_content.split('\n') if line.strip()]
            result = self._parse_mini_map_recursive(lines, 0, 0)
            
            return result
            
        except Exception as e:
            print(f"生成知识图谱失败: {e}")
            return MiniMapResult()
    
    def _parse_mini_map_recursive(self, lines: List[str], start_index: int, current_level: int) -> MiniMapResult:
        """递归解析迷你地图"""
        result = MiniMapResult()
        
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # 计算当前行的标题级别
            level = self._get_header_level(line)
            
            if level == 0:
                i += 1
                continue  # 不是标题行，跳过
            
            if level <= current_level and i > start_index:
                # 遇到同级或更高级的标题，结束当前层级的解析
                break
            
            if level == current_level + 1:
                # 解析标题和URL
                title, url = self._parse_title_and_url(line)
                node = MiniMapResult(title=title, url=url)
                
                # 递归解析子节点
                child_result = self._parse_mini_map_recursive(lines, i + 1, level)
                node.nodes = child_result.nodes
                
                if result.title is None:
                    # 如果这是第一个节点，设置为根节点
                    result.title = node.title
                    result.url = node.url
                    result.nodes = node.nodes
                else:
                    # 否则添加到子节点列表
                    result.nodes.append(node)
                
                # 跳过已处理的子节点
                i += 1
                while i < len(lines):
                    child_level = self._get_header_level(lines[i].strip())
                    if child_level > level:
                        i += 1
                    else:
                        break
            else:
                i += 1
        
        return result
    
    def _get_header_level(self, line: str) -> int:
        """获取标题级别"""
        level = 0
        for char in line:
            if char == '#':
                level += 1
            else:
                break
        return level
    
    def _parse_title_and_url(self, line: str) -> tuple[str, str]:
        """解析标题和URL"""
        # 移除开头的#号和空格
        content = line.lstrip('#').strip()
        
        # 检查是否包含URL格式 "标题:文件"
        if ':' in content:
            parts = content.split(':', 2)
            title = parts[0].strip()
            url = parts[1].strip()
            return title, url
        
        return content, ""
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096) 