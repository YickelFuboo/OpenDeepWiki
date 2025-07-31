"""
MCP客户端

实现Model Context Protocol (MCP) 客户端功能
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
import websockets
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

class MCPClient:
    """MCP客户端"""
    
    def __init__(self, server_url: str = "ws://localhost:8001/ws"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.request_id_counter = 0
        self.pending_requests = {}
        self.notification_handlers = []
    
    async def connect(self):
        """连接到MCP服务器"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            logger.info(f"已连接到MCP服务器: {self.server_url}")
            
            # 启动消息处理循环
            asyncio.create_task(self._message_handler())
            
            # 发送初始化请求
            await self.initialize()
            
        except Exception as e:
            logger.error(f"连接MCP服务器失败: {str(e)}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("已断开MCP服务器连接")
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化连接"""
        request = MCPRequest(
            id=self._generate_request_id(),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "clientInfo": {
                    "name": "OpenDeepWiki MCP Client",
                    "version": "1.0.0"
                }
            }
        )
        
        response = await self._send_request(request)
        return response.get("result", {})
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        request = MCPRequest(
            id=self._generate_request_id(),
            method="tools/list"
        )
        
        response = await self._send_request(request)
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """调用工具"""
        request = MCPRequest(
            id=self._generate_request_id(),
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments or {}
            }
        )
        
        response = await self._send_request(request)
        return response.get("result", {})
    
    async def send_notification(self, notification: Dict[str, Any]):
        """发送通知"""
        request = MCPRequest(
            id=self._generate_request_id(),
            method="notifications/notify",
            params=notification
        )
        
        await self._send_request(request)
    
    def add_notification_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """添加通知处理器"""
        self.notification_handlers.append(handler)
    
    async def _send_request(self, request: MCPRequest) -> Dict[str, Any]:
        """发送请求"""
        if not self.connected:
            raise Exception("未连接到MCP服务器")
        
        # 存储待处理的请求
        self.pending_requests[request.id] = asyncio.Future()
        
        try:
            # 发送请求
            await self.websocket.send(request.json())
            
            # 等待响应
            response = await self.pending_requests[request.id]
            return response
        
        except Exception as e:
            logger.error(f"发送请求异常: {str(e)}")
            raise
        finally:
            # 清理待处理的请求
            if request.id in self.pending_requests:
                del self.pending_requests[request.id]
    
    async def _message_handler(self):
        """消息处理循环"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if "id" in data:
                        # 这是一个响应
                        await self._handle_response(data)
                    elif "method" in data:
                        # 这是一个通知
                        await self._handle_notification(data)
                    else:
                        logger.warning(f"未知消息格式: {data}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析异常: {str(e)}")
                except Exception as e:
                    logger.error(f"消息处理异常: {str(e)}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"消息处理循环异常: {str(e)}")
        finally:
            self.connected = False
    
    async def _handle_response(self, data: Dict[str, Any]):
        """处理响应"""
        response = MCPResponse(**data)
        
        if response.id in self.pending_requests:
            future = self.pending_requests[response.id]
            if not future.done():
                if response.error:
                    future.set_exception(Exception(response.error.get("message", "Unknown error")))
                else:
                    future.set_result(response.dict())
    
    async def _handle_notification(self, data: Dict[str, Any]):
        """处理通知"""
        method = data.get("method")
        params = data.get("params", {})
        
        if method == "notifications/notify":
            # 调用所有通知处理器
            for handler in self.notification_handlers:
                try:
                    handler(params)
                except Exception as e:
                    logger.error(f"通知处理器异常: {str(e)}")
        
        logger.info(f"收到通知: {method}")
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        self.request_id_counter += 1
        return f"req_{self.request_id_counter}"
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "connected": self.connected,
            "server_url": self.server_url,
            "pending_requests": len(self.pending_requests),
            "notification_handlers": len(self.notification_handlers)
        }

# 使用示例
async def example_usage():
    """使用示例"""
    async with MCPClient() as client:
        # 获取工具列表
        tools = await client.list_tools()
        print(f"可用工具: {tools}")
        
        # 调用工具
        if tools:
            tool_name = tools[0]["name"]
            result = await client.call_tool(tool_name, {"param": "value"})
            print(f"工具调用结果: {result}")
        
        # 添加通知处理器
        def notification_handler(notification):
            print(f"收到通知: {notification}")
        
        client.add_notification_handler(notification_handler)
        
        # 发送通知
        await client.send_notification({"type": "test", "message": "Hello MCP!"})

if __name__ == "__main__":
    asyncio.run(example_usage()) 