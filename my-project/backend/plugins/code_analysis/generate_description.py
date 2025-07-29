"""
描述生成插件

根据项目代码和结构，自动生成项目描述
"""

import logging
from typing import Dict, Any, List
from semantic_kernel import Kernel
from semantic_kernel.skill_definition import sk_function

logger = logging.getLogger(__name__)

class GenerateDescriptionPlugin:
    """描述生成插件"""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
    
    @sk_function(
        description="根据项目代码和结构生成项目描述",
        name="generate_description"
    )
    def generate_description(self, context: Dict[str, Any]) -> str:
        """
        生成项目描述
        
        Args:
            context: 包含项目信息的上下文
            
        Returns:
            生成的项目描述
        """
        try:
            # 获取项目信息
            project_name = context.get("project_name", "Unknown Project")
            project_files = context.get("files", [])
            project_structure = context.get("structure", "")
            project_type = context.get("project_type", "unknown")
            
            # 构建提示词
            prompt = f"""
            请为项目 "{project_name}" 生成一个简洁而专业的项目描述。
            
            项目类型：{project_type}
            项目文件：{', '.join(project_files[:20])}
            项目结构：{project_structure}
            
            要求：
            1. 描述要简洁明了，不超过200字
            2. 突出项目的主要功能和特点
            3. 使用专业的技术术语
            4. 适合放在README文件的开头
            5. 包含项目的核心价值
            
            请生成项目描述。
            """
            
            # 调用AI生成描述
            result = self.kernel.run(prompt)
            return result
            
        except Exception as e:
            logger.error(f"生成项目描述异常: {str(e)}")
            return f"生成项目描述时发生错误: {str(e)}"
    
    @sk_function(
        description="根据项目类型生成特定格式的描述",
        name="generate_typed_description"
    )
    def generate_typed_description(self, context: Dict[str, Any]) -> str:
        """
        根据项目类型生成特定格式的描述
        
        Args:
            context: 包含项目信息的上下文
            
        Returns:
            生成的项目描述
        """
        try:
            project_type = context.get("project_type", "general")
            project_name = context.get("project_name", "Unknown Project")
            
            # 根据项目类型选择不同的模板
            templates = {
                "framework": self._get_framework_template(),
                "library": self._get_library_template(),
                "application": self._get_application_template(),
                "cli_tool": self._get_cli_template(),
                "development_tool": self._get_dev_tool_template(),
                "general": self._get_general_template()
            }
            
            template = templates.get(project_type, templates["general"])
            
            # 填充模板
            description = template.format(
                project_name=project_name,
                **context
            )
            
            return description
            
        except Exception as e:
            logger.error(f"生成类型化描述异常: {str(e)}")
            return f"生成类型化描述时发生错误: {str(e)}"
    
    def _get_framework_template(self) -> str:
        """获取框架描述模板"""
        return """
{project_name} 是一个现代化的框架，提供强大的功能和灵活的扩展性。

主要特性：
- 高性能和可扩展的架构设计
- 丰富的API和组件库
- 完善的文档和示例
- 活跃的社区支持
- 跨平台兼容性

适用于构建大型应用程序和系统。
"""
    
    def _get_library_template(self) -> str:
        """获取库描述模板"""
        return """
{project_name} 是一个实用的库，提供常用功能的封装和工具函数。

主要功能：
- 简化常见开发任务
- 提供可复用的组件
- 优化性能和内存使用
- 支持多种使用场景
- 易于集成和扩展

帮助开发者提高开发效率和代码质量。
"""
    
    def _get_application_template(self) -> str:
        """获取应用程序描述模板"""
        return """
{project_name} 是一个功能完整的应用程序，提供优秀的用户体验。

主要功能：
- 直观的用户界面设计
- 强大的功能特性
- 高性能和稳定性
- 安全可靠的数据处理
- 跨平台支持

为用户提供便捷和高效的解决方案。
"""
    
    def _get_cli_template(self) -> str:
        """获取CLI工具描述模板"""
        return """
{project_name} 是一个强大的命令行工具，提供高效的终端操作体验。

主要功能：
- 简洁的命令行接口
- 丰富的参数选项
- 快速的处理速度
- 详细的帮助文档
- 支持脚本自动化

提高开发者的工作效率和操作便利性。
"""
    
    def _get_dev_tool_template(self) -> str:
        """获取开发工具描述模板"""
        return """
{project_name} 是一个专业的开发工具，帮助开发者提高开发效率。

主要功能：
- 自动化开发流程
- 代码质量检查
- 性能优化建议
- 调试和测试支持
- 团队协作功能

为开发团队提供完整的开发工具链支持。
"""
    
    def _get_general_template(self) -> str:
        """获取通用描述模板"""
        return """
{project_name} 是一个专业的项目，提供实用的功能和解决方案。

主要特点：
- 功能完善且易于使用
- 代码质量高且可维护
- 文档详细且示例丰富
- 社区活跃且支持及时
- 持续更新和改进

为开发者提供可靠的技术解决方案。
""" 