"""
MCP服务器

实现Model Context Protocol (MCP) 服务器功能
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    """MCP请求模型"""
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """MCP响应模型"""
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPServer:
    """MCP服务器"""
    
    def __init__(self):
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.tools = {}
        self.connections = []
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket(websocket)
        
        @self.app.get("/")
        async def root():
            return {"message": "MCP Server is running"}
        
        @self.app.get("/tools")
        async def get_tools():
            return {"tools": list(self.tools.keys())}
    
    async def handle_websocket(self, websocket: WebSocket):
        """处理WebSocket连接"""
        await websocket.accept()
        self.connections.append(websocket)
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                
                # 解析请求
                try:
                    request = MCPRequest.parse_raw(data)
                    response = await self.handle_request(request)
                    await websocket.send_text(response.json())
                except Exception as e:
                    logger.error(f"处理MCP请求异常: {str(e)}")
                    error_response = MCPResponse(
                        id=request.id if 'request' in locals() else "unknown",
                        error={
                            "code": -1,
                            "message": str(e)
                        }
                    )
                    await websocket.send_text(error_response.json())
        
        except WebSocketDisconnect:
            logger.info("WebSocket连接断开")
        finally:
            if websocket in self.connections:
                self.connections.remove(websocket)
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理MCP请求"""
        try:
            if request.method == "initialize":
                return await self.handle_initialize(request)
            elif request.method == "tools/list":
                return await self.handle_tools_list(request)
            elif request.method == "tools/call":
                return await self.handle_tools_call(request)
            elif request.method == "notifications/notify":
                return await self.handle_notification(request)
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
        
        except Exception as e:
            logger.error(f"处理请求异常: {str(e)}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """处理初始化请求"""
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "OpenDeepWiki MCP Server",
                    "version": "1.0.0"
                }
            }
        )
    
    async def handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """处理工具列表请求"""
        tools = []
        
        for tool_name, tool in self.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.get("description", ""),
                "inputSchema": tool.get("input_schema", {})
            })
        
        return MCPResponse(
            id=request.id,
            result={
                "tools": tools
            }
        )
    
    async def handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """处理工具调用请求"""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            )
        
        try:
            # 调用工具
            tool = self.tools[tool_name]
            result = await tool["handler"](arguments)
            
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            )
        
        except Exception as e:
            logger.error(f"工具调用异常: {str(e)}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            )
    
    async def handle_notification(self, request: MCPRequest) -> MCPResponse:
        """处理通知请求"""
        # 处理通知，这里可以广播给所有连接的客户端
        return MCPResponse(
            id=request.id,
            result={"status": "ok"}
        )
    
    def register_tool(self, name: str, description: str, handler, input_schema: Dict[str, Any] = None):
        """注册工具"""
        self.tools[name] = {
            "description": description,
            "handler": handler,
            "input_schema": input_schema or {}
        }
        logger.info(f"注册MCP工具: {name}")
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"注销MCP工具: {name}")
    
    async def broadcast_notification(self, notification: Dict[str, Any]):
        """广播通知"""
        message = {
            "jsonrpc": "2.0",
            "method": "notifications/notify",
            "params": notification
        }
        
        for connection in self.connections:
            try:
                await connection.send_text(str(message))
            except Exception as e:
                logger.error(f"广播通知异常: {str(e)}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "name": "OpenDeepWiki MCP Server",
            "version": "1.0.0",
            "tools_count": len(self.tools),
            "connections_count": len(self.connections)
        }
    
    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """运行服务器"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port) 