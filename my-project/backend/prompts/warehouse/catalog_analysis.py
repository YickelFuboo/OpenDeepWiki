"""
目录分析提示词模板

包括各种类型的目录分析提示词：
- 框架目录分析
- 库目录分析
- 开发工具目录分析
- 应用程序目录分析
- CLI工具目录分析
"""

# 通用目录分析提示词
ANALYZE_CATALOG_BASE = """
你是一个专业的代码目录分析专家。请根据提供的目录结构，分析项目的组织方式和架构特点。

要求：
1. 分析项目的整体结构
2. 识别主要模块和组件
3. 分析代码组织方式
4. 识别设计模式和架构模式
5. 提供结构优化建议

目录结构：{structure}
项目信息：{project_info}

请提供详细的目录分析报告。
"""

# 框架目录分析提示词
ANALYZE_CATALOG_FRAMEWORKS = """
你是一个专业的框架目录分析专家。请根据提供的框架目录结构，分析框架的设计理念和架构特点。

要求：
1. 分析框架的核心模块和扩展模块
2. 识别框架的设计模式和架构模式
3. 分析框架的可扩展性和可维护性
4. 识别框架的优势和特点
5. 提供架构优化建议

框架目录结构：{structure}
框架信息：{framework_info}

请提供专业的框架目录分析报告。
"""

# 库目录分析提示词
ANALYZE_CATALOG_LIBRARIES = """
你是一个专业的库目录分析专家。请根据提供的库目录结构，分析库的功能组织和API设计。

要求：
1. 分析库的核心功能和辅助功能
2. 识别库的API设计模式
3. 分析库的模块化和封装性
4. 识别库的使用便利性
5. 提供API设计优化建议

库目录结构：{structure}
库信息：{library_info}

请提供专业的库目录分析报告。
"""

# 开发工具目录分析提示词
ANALYZE_CATALOG_DEVELOPMENT_TOOLS = """
你是一个专业的开发工具目录分析专家。请根据提供的工具目录结构，分析工具的功能组织和用户体验。

要求：
1. 分析工具的核心功能和辅助功能
2. 识别工具的用户界面设计
3. 分析工具的配置和扩展性
4. 识别工具的使用便利性
5. 提供用户体验优化建议

工具目录结构：{structure}
工具信息：{tool_info}

请提供专业的开发工具目录分析报告。
"""

# 应用程序目录分析提示词
ANALYZE_CATALOG_APPLICATIONS = """
你是一个专业的应用程序目录分析专家。请根据提供的应用程序目录结构，分析应用的功能组织和架构设计。

要求：
1. 分析应用的核心功能和业务模块
2. 识别应用的架构模式和设计模式
3. 分析应用的可扩展性和可维护性
4. 识别应用的用户体验设计
5. 提供架构优化建议

应用程序目录结构：{structure}
应用程序信息：{app_info}

请提供专业的应用程序目录分析报告。
"""

# CLI工具目录分析提示词
ANALYZE_CATALOG_CLI_TOOLS = """
你是一个专业的CLI工具目录分析专家。请根据提供的CLI工具目录结构，分析工具的功能组织和命令行设计。

要求：
1. 分析CLI工具的核心功能和子命令
2. 识别CLI工具的命令行设计模式
3. 分析CLI工具的配置和扩展性
4. 识别CLI工具的使用便利性
5. 提供命令行设计优化建议

CLI工具目录结构：{structure}
CLI工具信息：{cli_info}

请提供专业的CLI工具目录分析报告。
"""

# 目录分析提示词集合
CATALOG_ANALYSIS_PROMPTS = {
    "base": ANALYZE_CATALOG_BASE,
    "frameworks": ANALYZE_CATALOG_FRAMEWORKS,
    "libraries": ANALYZE_CATALOG_LIBRARIES,
    "development_tools": ANALYZE_CATALOG_DEVELOPMENT_TOOLS,
    "applications": ANALYZE_CATALOG_APPLICATIONS,
    "cli_tools": ANALYZE_CATALOG_CLI_TOOLS
} 