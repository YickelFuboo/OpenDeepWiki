import re
import json
from typing import List, Dict, Any
from fastapi import FastAPI
from loguru import logger

from src.core.config import settings
from src.mcp.tools.warehouse_tool import WarehouseTool


class Tool:
    """MCP工具定义"""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema


class MCPExtensions:
    """MCP扩展"""
    
    @staticmethod
    def add_koala_mcp(app: FastAPI):
        """添加Koala MCP服务"""
        try:
            # 注册仓库工具
            app.state.warehouse_tool = WarehouseTool()
            
            logger.info("MCP扩展已添加")
            return app
            
        except Exception as e:
            logger.error(f"添加MCP扩展失败: {e}")
            raise
    
    @staticmethod
    def create_tools(owner: str, name: str) -> List[Tool]:
        """创建工具列表"""
        tools = []
        
        # 生成文档工具
        descript = f"Generate detailed technical documentation for the {owner}/{name} GitHub repository based on user inquiries. Analyzes repository structure, code components, APIs, dependencies, and implementation patterns to create comprehensive developer documentation with troubleshooting guides, architecture explanations, customization options, and implementation insights."
        
        input_schema = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": f"The relevant keywords for your retrieval of {owner}/{name} or a question content"
                }
            },
            "required": ["question"]
        }
        
        # 清理MCP名称
        mcp_name = f"{owner}_{name}"
        mcp_name = re.sub(r'[^a-zA-Z0-9]', '', mcp_name)
        mcp_name = mcp_name[:50] if len(mcp_name) > 50 else mcp_name
        mcp_name = mcp_name.lower()
        
        # 添加生成文档工具
        tools.append(Tool(
            name=f"{mcp_name}_GenerateDocument",
            description=descript,
            input_schema=input_schema
        ))
        
        # 如果启用了Mem0，添加搜索工具
        if hasattr(settings, 'enable_mem0') and settings.enable_mem0:
            search_tool_schema = {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Detailed description of the code or documentation you need. Specify whether you're looking for a function, class, method, or specific documentation. Be as specific as possible to improve search accuracy."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of search results to return. Default is 5. Increase for broader coverage or decrease for focused results.",
                        "default": 5
                    },
                    "minRelevance": {
                        "type": "number",
                        "description": "Minimum relevance threshold for vector search results, ranging from 0 to 1. Default is 0.3. Higher values (e.g., 0.7) return more precise matches, while lower values provide more varied results.",
                        "default": 0.3
                    }
                },
                "required": ["query"]
            }
            
            tools.append(Tool(
                name=f"{mcp_name}-Search",
                description=f"Query {owner}/{name} repository for relevant code snippets and documentation based on user inquiries.",
                input_schema=search_tool_schema
            ))
        
        # 添加文件读取工具
        file_read_schema = {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "The starting line number (1-based)"
                },
                "end_line": {
                    "type": "integer",
                    "description": "The ending line number (inclusive)"
                }
            },
            "required": ["file_path", "start_line", "end_line"]
        }
        
        tools.append(Tool(
            name=f"{mcp_name}-ReadFileFromLine",
            description="Returns the file content from the specified starting line to the ending line (inclusive). If the total output length exceeds 10,000 characters, only the first 10,000 characters are returned, the content order is consistent with the original file, and the original line breaks are retained.",
            input_schema=file_read_schema
        ))
        
        return tools
    
    @staticmethod
    async def handle_tool_call(tool_name: str, parameters: Dict[str, Any], db_session) -> str:
        """处理工具调用"""
        try:
            if tool_name.endswith("_GenerateDocument"):
                # 生成文档
                warehouse_tool = WarehouseTool(db_session)
                question = parameters.get("question", "")
                return await warehouse_tool.generate_document(question)
            
            elif tool_name.endswith("-Search"):
                # 搜索功能
                query = parameters.get("query", "")
                limit = parameters.get("limit", 5)
                min_relevance = parameters.get("minRelevance", 0.3)
                return await MCPExtensions._handle_search(query, limit, min_relevance)
            
            elif tool_name.endswith("-ReadFileFromLine"):
                # 读取文件
                file_path = parameters.get("file_path", "")
                start_line = parameters.get("start_line", 1)
                end_line = parameters.get("end_line", 1)
                return await MCPExtensions._handle_read_file(file_path, start_line, end_line)
            
            else:
                return f"未知工具: {tool_name}"
                
        except Exception as e:
            logger.error(f"处理工具调用失败: {e}")
            return f"工具调用失败: {str(e)}"
    
    @staticmethod
    async def _handle_search(query: str, limit: int, min_relevance: float) -> str:
        """处理搜索请求"""
        # 这里实现搜索逻辑
        return f"搜索结果: {query} (限制: {limit}, 最小相关性: {min_relevance})"
    
    @staticmethod
    async def _handle_read_file(file_path: str, start_line: int, end_line: int) -> str:
        """处理文件读取请求"""
        try:
            import os
            if not os.path.exists(file_path):
                return f"文件不存在: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return f"行号范围无效: {start_line}-{end_line}"
            
            content = ''.join(lines[start_line-1:end_line])
            
            # 限制输出长度
            if len(content) > 10000:
                content = content[:10000] + "\n... (内容已截断)"
            
            return content
            
        except Exception as e:
            return f"读取文件失败: {str(e)}" 