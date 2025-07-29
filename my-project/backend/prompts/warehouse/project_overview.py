"""
项目概览提示词模板

包括各种类型的项目概览提示词：
- 框架概览
- 库概览
- 开发工具概览
- 应用程序概览
- CLI工具概览
"""

# 通用项目概览提示词
PROJECT_OVERVIEW_BASE = """
你是一个专业的项目分析专家。请根据提供的项目信息，生成详细的项目概览。

要求：
1. 分析项目的整体架构和设计理念
2. 总结项目的主要功能和特性
3. 评估项目的技术栈和依赖关系
4. 分析项目的代码质量和可维护性
5. 提供项目的发展建议和最佳实践

项目信息：{project_info}
文件结构：{file_structure}
主要文件：{main_files}

请生成专业的项目概览报告。
"""

# 框架项目概览提示词
FRAMEWORK_OVERVIEW = """
你是一个专业的框架分析专家。请分析这个框架项目的架构和特性。

要求：
1. 分析框架的设计理念和架构模式
2. 总结框架的核心功能和扩展点
3. 评估框架的性能和可扩展性
4. 分析框架的生态系统和社区支持
5. 提供框架的使用建议和最佳实践

框架信息：{framework_info}
框架结构：{framework_structure}
核心文件：{core_files}

请生成专业的框架概览报告。
"""

# 库项目概览提示词
LIBRARY_OVERVIEW = """
你是一个专业的库分析专家。请分析这个库项目的功能和特性。

要求：
1. 分析库的功能定位和适用场景
2. 总结库的主要API和功能模块
3. 评估库的易用性和文档质量
4. 分析库的依赖关系和兼容性
5. 提供库的使用建议和示例

库信息：{library_info}
库结构：{library_structure}
API文件：{api_files}

请生成专业的库概览报告。
"""

# 开发工具项目概览提示词
DEVELOPMENT_TOOL_OVERVIEW = """
你是一个专业的开发工具分析专家。请分析这个开发工具项目的功能。

要求：
1. 分析工具的功能定位和使用场景
2. 总结工具的主要功能和配置选项
3. 评估工具的易用性和集成能力
4. 分析工具的性能和稳定性
5. 提供工具的使用建议和配置最佳实践

工具信息：{tool_info}
工具结构：{tool_structure}
配置文件：{config_files}

请生成专业的开发工具概览报告。
"""

# 应用程序项目概览提示词
APPLICATION_OVERVIEW = """
你是一个专业的应用程序分析专家。请分析这个应用程序项目的功能。

要求：
1. 分析应用的功能定位和用户群体
2. 总结应用的主要功能和用户界面
3. 评估应用的用户体验和性能
4. 分析应用的技术架构和部署方式
5. 提供应用的使用建议和优化建议

应用信息：{app_info}
应用结构：{app_structure}
主要组件：{main_components}

请生成专业的应用程序概览报告。
"""

# CLI工具项目概览提示词
CLI_TOOL_OVERVIEW = """
你是一个专业的CLI工具分析专家。请分析这个命令行工具项目的功能。

要求：
1. 分析CLI工具的功能定位和使用场景
2. 总结工具的命令行接口和参数选项
3. 评估工具的易用性和帮助文档
4. 分析工具的性能和错误处理
5. 提供工具的使用建议和脚本示例

CLI工具信息：{cli_info}
CLI工具结构：{cli_structure}
命令文件：{command_files}

请生成专业的CLI工具概览报告。
"""

# 项目概览提示词集合
PROJECT_OVERVIEW_PROMPTS = {
    "base": PROJECT_OVERVIEW_BASE,
    "framework": FRAMEWORK_OVERVIEW,
    "library": LIBRARY_OVERVIEW,
    "development_tool": DEVELOPMENT_TOOL_OVERVIEW,
    "application": APPLICATION_OVERVIEW,
    "cli_tool": CLI_TOOL_OVERVIEW
} 