"""
文档生成提示词模板

包括各种类型的文档生成提示词：
- 框架文档生成
- 库文档生成
- 开发工具文档生成
- 应用程序文档生成
- CLI工具文档生成
"""

# 通用文档生成提示词
GENERATE_DOCS_BASE = """
你是一个专业的代码文档生成专家。请根据提供的代码文件和目录结构，生成高质量的文档。

要求：
1. 文档结构清晰，层次分明
2. 包含项目概述、安装说明、使用方法
3. 提供代码示例和API说明
4. 使用Markdown格式
5. 语言简洁明了，易于理解

代码文件：{files}
目录结构：{structure}
项目信息：{project_info}

请生成完整的项目文档。
"""

# 框架文档生成提示词
GENERATE_DOCS_FRAMEWORKS = """
你是一个专业的框架文档生成专家。请根据提供的框架代码，生成详细的框架文档。

要求：
1. 详细说明框架的设计理念和架构
2. 提供完整的API文档
3. 包含使用示例和最佳实践
4. 说明框架的优势和适用场景
5. 提供性能优化建议

框架代码：{code}
框架结构：{structure}
框架信息：{framework_info}

请生成专业的框架文档。
"""

# 库文档生成提示词
GENERATE_DOCS_LIBRARIES = """
你是一个专业的库文档生成专家。请根据提供的库代码，生成详细的库文档。

要求：
1. 详细说明库的功能和特性
2. 提供完整的API参考文档
3. 包含使用示例和代码片段
4. 说明依赖关系和兼容性
5. 提供错误处理和调试指南

库代码：{code}
库结构：{structure}
库信息：{library_info}

请生成专业的库文档。
"""

# 开发工具文档生成提示词
GENERATE_DOCS_DEVELOPMENT_TOOLS = """
你是一个专业的开发工具文档生成专家。请根据提供的工具代码，生成详细的使用文档。

要求：
1. 详细说明工具的功能和用途
2. 提供完整的安装和配置说明
3. 包含使用示例和命令行参数
4. 说明工具的配置选项
5. 提供故障排除指南

工具代码：{code}
工具结构：{structure}
工具信息：{tool_info}

请生成专业的开发工具文档。
"""

# 应用程序文档生成提示词
GENERATE_DOCS_APPLICATIONS = """
你是一个专业的应用程序文档生成专家。请根据提供的应用程序代码，生成详细的用户文档。

要求：
1. 详细说明应用程序的功能和特性
2. 提供完整的用户使用指南
3. 包含界面截图和操作说明
4. 说明系统要求和安装步骤
5. 提供常见问题解答

应用程序代码：{code}
应用程序结构：{structure}
应用程序信息：{app_info}

请生成专业的应用程序文档。
"""

# CLI工具文档生成提示词
GENERATE_DOCS_CLI_TOOLS = """
你是一个专业的CLI工具文档生成专家。请根据提供的CLI工具代码，生成详细的使用文档。

要求：
1. 详细说明CLI工具的功能和用途
2. 提供完整的命令行参数说明
3. 包含使用示例和命令组合
4. 说明工具的配置选项
5. 提供错误处理和调试指南

CLI工具代码：{code}
CLI工具结构：{structure}
CLI工具信息：{cli_info}

请生成专业的CLI工具文档。
"""

# 文档生成提示词集合
DOCUMENT_GENERATION_PROMPTS = {
    "base": GENERATE_DOCS_BASE,
    "frameworks": GENERATE_DOCS_FRAMEWORKS,
    "libraries": GENERATE_DOCS_LIBRARIES,
    "development_tools": GENERATE_DOCS_DEVELOPMENT_TOOLS,
    "applications": GENERATE_DOCS_APPLICATIONS,
    "cli_tools": GENERATE_DOCS_CLI_TOOLS
} 