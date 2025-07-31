"""
README生成插件

根据项目代码和结构，自动生成README文档
"""

import os
from typing import Dict, Any, List
from semantic_kernel import Kernel
from semantic_kernel.skill_definition import sk_function

class GenerateReadmePlugin:
    """README生成插件"""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
    
    @sk_function(
        description="根据项目代码和结构生成README文档",
        name="generate_readme"
    )
    def generate_readme(self, context: Dict[str, Any]) -> str:
        """
        生成README文档
        
        Args:
            context: 包含项目信息的上下文
            
        Returns:
            生成的README文档内容
        """
        try:
            # 获取项目信息
            project_name = context.get("project_name", "Unknown Project")
            project_description = context.get("description", "")
            project_structure = context.get("structure", "")
            project_files = context.get("files", [])
            
            # 构建提示词
            prompt = f"""
            请为项目 "{project_name}" 生成一个专业的README文档。
            
            项目描述：{project_description}
            项目结构：{project_structure}
            主要文件：{', '.join(project_files[:10])}
            
            要求：
            1. 包含项目概述和特性
            2. 提供安装和使用说明
            3. 包含代码示例
            4. 说明贡献方式
            5. 包含许可证信息
            6. 使用Markdown格式
            
            请生成完整的README文档。
            """
            
            # 调用AI生成README
            result = self.kernel.run(prompt)
            return result
            
        except Exception as e:
            return f"生成README时发生错误: {str(e)}"
    
    @sk_function(
        description="根据项目类型生成特定格式的README",
        name="generate_typed_readme"
    )
    def generate_typed_readme(self, context: Dict[str, Any]) -> str:
        """
        根据项目类型生成特定格式的README
        
        Args:
            context: 包含项目信息的上下文
            
        Returns:
            生成的README文档内容
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
                "general": self._get_general_template()
            }
            
            template = templates.get(project_type, templates["general"])
            
            # 填充模板
            readme_content = template.format(
                project_name=project_name,
                **context
            )
            
            return readme_content
            
        except Exception as e:
            return f"生成类型化README时发生错误: {str(e)}"
    
    def _get_framework_template(self) -> str:
        """获取框架README模板"""
        return """
# {project_name}

一个强大的框架，提供现代化的开发体验。

## 特性

- 高性能和可扩展性
- 现代化的API设计
- 丰富的生态系统
- 完善的文档和示例

## 安装

```bash
npm install {project_name}
```

## 快速开始

```javascript
import { {project_name} } from '{project_name}';

const app = new {project_name}();
app.start();
```

## 文档

详细文档请访问：[文档链接]

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
"""
    
    def _get_library_template(self) -> str:
        """获取库README模板"""
        return """
# {project_name}

一个实用的JavaScript库，提供常用功能的封装。

## 安装

```bash
npm install {project_name}
```

## 使用方法

```javascript
import {{ {project_name} }} from '{project_name}';

// 使用示例
const result = {project_name}.someFunction();
```

## API文档

详细API文档请参考：[API文档链接]

## 许可证

MIT License
"""
    
    def _get_application_template(self) -> str:
        """获取应用程序README模板"""
        return """
# {project_name}

一个功能完整的应用程序。

## 功能特性

- 用户友好的界面
- 强大的功能
- 高性能
- 安全可靠

## 安装和运行

```bash
# 克隆项目
git clone https://github.com/user/{project_name}.git

# 安装依赖
npm install

# 启动应用
npm start
```

## 配置

详细配置说明请参考：[配置文档]

## 许可证

MIT License
"""
    
    def _get_cli_template(self) -> str:
        """获取CLI工具README模板"""
        return """
# {project_name}

一个强大的命令行工具。

## 安装

```bash
npm install -g {project_name}
```

## 使用方法

```bash
{project_name} [command] [options]
```

## 命令

- `init`: 初始化项目
- `build`: 构建项目
- `deploy`: 部署项目

## 配置

详细配置说明请参考：[配置文档]

## 许可证

MIT License
"""
    
    def _get_general_template(self) -> str:
        """获取通用README模板"""
        return """
# {project_name}

{description}

## 安装

```bash
npm install {project_name}
```

## 使用方法

```javascript
// 使用示例
```

## 文档

详细文档请参考：[文档链接]

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
""" 