import os
import json
from typing import Dict, Any, Optional
from loguru import logger


class PromptService:
    """提示词服务"""
    
    def __init__(self):
        self.prompts_cache = {}
        self.prompts_path = os.path.join(os.getcwd(), "prompts")
    
    async def get_prompt(self, prompt_name: str, parameters: Dict[str, Any] = None, 
                        model: str = None) -> str:
        """获取提示词内容"""
        try:
            # 检查缓存
            cache_key = f"{prompt_name}_{model or 'default'}"
            if cache_key in self.prompts_cache:
                prompt_template = self.prompts_cache[cache_key]
            else:
                # 从文件加载提示词
                prompt_template = await self._load_prompt_from_file(prompt_name)
                self.prompts_cache[cache_key] = prompt_template
            
            # 替换参数
            if parameters:
                prompt_content = prompt_template
                for key, value in parameters.items():
                    placeholder = f"{{{key}}}"
                    prompt_content = prompt_content.replace(placeholder, str(value))
                return prompt_content
            
            return prompt_template
            
        except Exception as e:
            logger.error(f"获取提示词失败: {e}")
            return f"获取提示词时发生错误: {str(e)}"
    
    async def _load_prompt_from_file(self, prompt_name: str) -> str:
        """从文件加载提示词"""
        try:
            # 解析提示词名称，获取类别和具体名称
            if "." in prompt_name:
                category, name = prompt_name.split(".", 1)
            else:
                category = "default"
                name = prompt_name
            
            # 构建文件路径
            file_path = os.path.join(self.prompts_path, category, f"{name}.md")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 如果文件不存在，返回默认提示词
                return self._get_default_prompt(prompt_name)
                
        except Exception as e:
            logger.error(f"加载提示词文件失败: {e}")
            return self._get_default_prompt(prompt_name)
    
    def _get_default_prompt(self, prompt_name: str) -> str:
        """获取默认提示词"""
        default_prompts = {
            "Warehouse.Overview": """请根据以下信息生成项目概述：

项目目录结构：
{catalogue}

Git仓库：{git_repository}
分支：{branch}

README内容：
{readme}

请生成一个详细的项目概述，包括：
1. 项目简介
2. 主要功能
3. 技术栈
4. 项目结构
5. 使用说明""",
            
            "Warehouse.OverviewApplications": """请分析以下应用程序项目：

项目目录结构：
{catalogue}

Git仓库：{git_repository}
分支：{branch}

README内容：
{readme}

请生成应用程序项目的概述，重点关注：
1. 应用类型和用途
2. 用户界面特点
3. 核心功能模块
4. 技术架构
5. 部署方式""",
            
            "Warehouse.OverviewLibraries": """请分析以下库项目：

项目目录结构：
{catalogue}

Git仓库：{git_repository}
分支：{branch}

README内容：
{readme}

请生成库项目的概述，重点关注：
1. 库的用途和功能
2. API设计特点
3. 依赖关系
4. 使用示例
5. 文档完整性""",
            
            "Warehouse.OverviewFrameworks": """请分析以下框架项目：

项目目录结构：
{catalogue}

Git仓库：{git_repository}
分支：{branch}

README内容：
{readme}

请生成框架项目的概述，重点关注：
1. 框架的设计理念
2. 核心组件
3. 扩展机制
4. 生态系统
5. 最佳实践""",
            
            "Chat.System": """你是一个智能代码分析助手，可以帮助用户分析代码仓库、回答技术问题、生成文档等。

请根据用户的问题提供准确、有用的回答。如果涉及代码分析，请确保：
1. 理解代码结构和逻辑
2. 识别潜在问题和改进建议
3. 提供清晰的解释和建议
4. 考虑代码的可维护性和性能""",
            
            "Mem0.DocsSystem": """你是一个文档系统助手，专门帮助用户管理和分析文档。

请根据用户的需求：
1. 分析文档结构和内容
2. 提供文档改进建议
3. 帮助生成文档模板
4. 回答文档相关问题""",
            
            "Mem0.CodeSystem": """你是一个代码系统助手，专门帮助用户分析和理解代码。

请根据用户的需求：
1. 分析代码结构和逻辑
2. 识别代码模式和设计
3. 提供代码改进建议
4. 解释复杂代码片段"""
        }
        
        return default_prompts.get(prompt_name, f"提示词 {prompt_name} 未找到")
    
    async def get_prompt_categories(self) -> Dict[str, list]:
        """获取提示词分类"""
        try:
            categories = {}
            
            if os.path.exists(self.prompts_path):
                for category in os.listdir(self.prompts_path):
                    category_path = os.path.join(self.prompts_path, category)
                    if os.path.isdir(category_path):
                        prompts = []
                        for file in os.listdir(category_path):
                            if file.endswith('.md'):
                                prompt_name = file[:-3]  # 移除.md扩展名
                                prompts.append({
                                    "name": prompt_name,
                                    "full_name": f"{category}.{prompt_name}",
                                    "file_path": os.path.join(category_path, file)
                                })
                        categories[category] = prompts
            
            return categories
            
        except Exception as e:
            logger.error(f"获取提示词分类失败: {e}")
            return {}
    
    async def create_prompt(self, category: str, name: str, content: str) -> bool:
        """创建新的提示词"""
        try:
            # 创建分类目录
            category_path = os.path.join(self.prompts_path, category)
            os.makedirs(category_path, exist_ok=True)
            
            # 创建提示词文件
            file_path = os.path.join(category_path, f"{name}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 清除缓存
            cache_key = f"{category}.{name}_default"
            if cache_key in self.prompts_cache:
                del self.prompts_cache[cache_key]
            
            logger.info(f"创建提示词成功: {category}.{name}")
            return True
            
        except Exception as e:
            logger.error(f"创建提示词失败: {e}")
            return False
    
    async def update_prompt(self, category: str, name: str, content: str) -> bool:
        """更新提示词"""
        try:
            file_path = os.path.join(self.prompts_path, category, f"{name}.md")
            
            if os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 清除缓存
                cache_key = f"{category}.{name}_default"
                if cache_key in self.prompts_cache:
                    del self.prompts_cache[cache_key]
                
                logger.info(f"更新提示词成功: {category}.{name}")
                return True
            else:
                logger.error(f"提示词文件不存在: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"更新提示词失败: {e}")
            return False
    
    async def delete_prompt(self, category: str, name: str) -> bool:
        """删除提示词"""
        try:
            file_path = os.path.join(self.prompts_path, category, f"{name}.md")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # 清除缓存
                cache_key = f"{category}.{name}_default"
                if cache_key in self.prompts_cache:
                    del self.prompts_cache[cache_key]
                
                logger.info(f"删除提示词成功: {category}.{name}")
                return True
            else:
                logger.error(f"提示词文件不存在: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"删除提示词失败: {e}")
            return False 