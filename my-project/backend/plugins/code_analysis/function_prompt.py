"""
函数提示插件

根据代码上下文生成函数提示和文档
"""

import logging
from typing import Dict, Any, List
from semantic_kernel import Kernel
from semantic_kernel.skill_definition import sk_function

logger = logging.getLogger(__name__)

class FunctionPromptPlugin:
    """函数提示插件"""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
    
    @sk_function(
        description="根据函数代码生成函数提示",
        name="generate_function_prompt"
    )
    def generate_function_prompt(self, context: Dict[str, Any]) -> str:
        """
        生成函数提示
        
        Args:
            context: 包含函数信息的上下文
            
        Returns:
            生成的函数提示
        """
        try:
            # 获取函数信息
            function_name = context.get("function_name", "Unknown Function")
            function_code = context.get("code", "")
            function_params = context.get("parameters", [])
            return_type = context.get("return_type", "void")
            language = context.get("language", "unknown")
            
            # 构建提示词
            prompt = f"""
            请为函数 "{function_name}" 生成详细的函数提示和文档。
            
            函数信息：
            - 名称：{function_name}
            - 返回类型：{return_type}
            - 参数：{', '.join(function_params)}
            - 语言：{language}
            
            函数代码：
            {function_code}
            
            要求：
            1. 生成详细的函数文档
            2. 说明函数的功能和用途
            3. 解释每个参数的作用
            4. 说明返回值的含义
            5. 提供使用示例
            6. 包含注意事项和最佳实践
            
            请生成专业的函数提示文档。
            """
            
            # 调用AI生成函数提示
            result = self.kernel.run(prompt)
            return result
            
        except Exception as e:
            logger.error(f"生成函数提示异常: {str(e)}")
            return f"生成函数提示时发生错误: {str(e)}"
    
    @sk_function(
        description="根据函数类型生成特定格式的提示",
        name="generate_typed_function_prompt"
    )
    def generate_typed_function_prompt(self, context: Dict[str, Any]) -> str:
        """
        根据函数类型生成特定格式的提示
        
        Args:
            context: 包含函数信息的上下文
            
        Returns:
            生成的函数提示
        """
        try:
            function_type = context.get("function_type", "general")
            function_name = context.get("function_name", "Unknown Function")
            
            # 根据函数类型选择不同的模板
            templates = {
                "utility": self._get_utility_template(),
                "api": self._get_api_template(),
                "data_processing": self._get_data_processing_template(),
                "validation": self._get_validation_template(),
                "formatting": self._get_formatting_template(),
                "general": self._get_general_template()
            }
            
            template = templates.get(function_type, templates["general"])
            
            # 填充模板
            prompt = template.format(
                function_name=function_name,
                **context
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"生成类型化函数提示异常: {str(e)}")
            return f"生成类型化函数提示时发生错误: {str(e)}"
    
    @sk_function(
        description="生成函数参数提示",
        name="generate_parameter_prompt"
    )
    def generate_parameter_prompt(self, context: Dict[str, Any]) -> str:
        """
        生成函数参数提示
        
        Args:
            context: 包含参数信息的上下文
            
        Returns:
            生成的参数提示
        """
        try:
            parameters = context.get("parameters", [])
            function_name = context.get("function_name", "Unknown Function")
            
            prompt = f"""
            请为函数 "{function_name}" 的参数生成详细的提示说明。
            
            参数列表：{parameters}
            
            要求：
            1. 为每个参数提供详细说明
            2. 说明参数的数据类型和格式
            3. 提供参数的默认值（如果有）
            4. 说明参数的可选性和约束条件
            5. 提供参数的使用示例
            6. 包含参数验证规则
            
            请生成专业的参数提示文档。
            """
            
            result = self.kernel.run(prompt)
            return result
            
        except Exception as e:
            logger.error(f"生成参数提示异常: {str(e)}")
            return f"生成参数提示时发生错误: {str(e)}"
    
    def _get_utility_template(self) -> str:
        """获取工具函数模板"""
        return """
# {function_name} - 工具函数

## 功能描述
{function_name} 是一个实用的工具函数，用于{description}。

## 参数说明
{parameters}

## 返回值
{return_value}

## 使用示例
```{language}
{example}
```

## 注意事项
- {notes}
"""
    
    def _get_api_template(self) -> str:
        """获取API函数模板"""
        return """
# {function_name} - API函数

## 接口描述
{function_name} 是一个API接口函数，用于{description}。

## 请求参数
{parameters}

## 响应格式
{return_value}

## 调用示例
```{language}
{example}
```

## 错误处理
{error_handling}
"""
    
    def _get_data_processing_template(self) -> str:
        """获取数据处理函数模板"""
        return """
# {function_name} - 数据处理函数

## 处理功能
{function_name} 是一个数据处理函数，用于{description}。

## 输入参数
{parameters}

## 输出结果
{return_value}

## 处理示例
```{language}
{example}
```

## 性能说明
{performance_notes}
"""
    
    def _get_validation_template(self) -> str:
        """获取验证函数模板"""
        return """
# {function_name} - 验证函数

## 验证功能
{function_name} 是一个验证函数，用于{description}。

## 验证参数
{parameters}

## 验证结果
{return_value}

## 验证示例
```{language}
{example}
```

## 验证规则
{validation_rules}
"""
    
    def _get_formatting_template(self) -> str:
        """获取格式化函数模板"""
        return """
# {function_name} - 格式化函数

## 格式化功能
{function_name} 是一个格式化函数，用于{description}。

## 格式化参数
{parameters}

## 格式化结果
{return_value}

## 格式化示例
```{language}
{example}
```

## 格式化选项
{formatting_options}
"""
    
    def _get_general_template(self) -> str:
        """获取通用函数模板"""
        return """
# {function_name} - 函数文档

## 功能说明
{function_name} 用于{description}。

## 参数列表
{parameters}

## 返回值
{return_value}

## 使用示例
```{language}
{example}
```

## 相关说明
{related_notes}
""" 