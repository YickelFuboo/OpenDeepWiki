"""
思维导图生成提示词模板

包括各种类型的思维导图生成提示词：
- 项目结构思维导图
- 代码架构思维导图
- 功能模块思维导图
- 技术栈思维导图
"""

# 通用思维导图生成提示词
MINDMAP_GENERATION_BASE = """
你是一个专业的思维导图生成专家。请根据提供的项目信息，生成清晰的思维导图。

要求：
1. 思维导图结构清晰，层次分明
2. 使用Mermaid语法格式
3. 包含主要节点和子节点
4. 使用合适的颜色和图标
5. 突出重点和关键信息

项目信息：{project_info}
文件结构：{file_structure}
主要功能：{main_features}

请生成专业的思维导图。
"""

# 项目结构思维导图生成提示词
PROJECT_STRUCTURE_MINDMAP = """
你是一个专业的项目结构分析专家。请根据项目结构生成思维导图。

要求：
1. 以项目根目录为中心
2. 按目录层次组织节点
3. 突出重要文件和目录
4. 使用不同的颜色区分文件类型
5. 包含文件数量统计

项目结构：{structure}
文件统计：{file_stats}
重要文件：{important_files}

请生成项目结构思维导图。
"""

# 代码架构思维导图生成提示词
CODE_ARCHITECTURE_MINDMAP = """
你是一个专业的代码架构分析专家。请根据代码架构生成思维导图。

要求：
1. 以系统架构为中心
2. 按模块和组件组织
3. 显示模块间的关系
4. 突出核心组件
5. 包含技术栈信息

架构信息：{architecture_info}
模块关系：{module_relations}
技术栈：{tech_stack}

请生成代码架构思维导图。
"""

# 功能模块思维导图生成提示词
FUNCTIONAL_MODULES_MINDMAP = """
你是一个专业的功能模块分析专家。请根据功能模块生成思维导图。

要求：
1. 以核心功能为中心
2. 按功能模块组织
3. 显示功能间的关系
4. 突出主要功能
5. 包含功能描述

功能模块：{functional_modules}
功能关系：{function_relations}
核心功能：{core_functions}

请生成功能模块思维导图。
"""

# 技术栈思维导图生成提示词
TECH_STACK_MINDMAP = """
你是一个专业的技术栈分析专家。请根据技术栈生成思维导图。

要求：
1. 以技术栈为中心
2. 按技术类别组织
3. 显示技术间的关系
4. 突出核心技术
5. 包含版本信息

技术栈：{tech_stack}
技术关系：{tech_relations}
核心技术：{core_technologies}

请生成技术栈思维导图。
"""

# 思维导图生成提示词集合
MINDMAP_GENERATION_PROMPTS = {
    "base": MINDMAP_GENERATION_BASE,
    "project_structure": PROJECT_STRUCTURE_MINDMAP,
    "code_architecture": CODE_ARCHITECTURE_MINDMAP,
    "functional_modules": FUNCTIONAL_MODULES_MINDMAP,
    "tech_stack": TECH_STACK_MINDMAP
} 