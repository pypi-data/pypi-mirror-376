"""
MCP服务器生成器核心模块

提供MCP服务器文件生成的核心功能
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class MCPGenerator:
    """MCP服务器生成器类"""
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def generate(
        self,
        output_path: str,
        service_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_param_name: str = "path",
        tool_param_type: str = "str",
        tool_return_type: str = "str",
        tool_description: str = "MCP工具",
        tool_code: str = "# TODO Implement code logic\n    output = \"...\"",
        service_port: Optional[int] = None,
        author: str = "开发者"
    ) -> bool:
        """
        生成MCP服务器文件
        
        Args:
            output_path: 输出文件路径
            service_name: 服务名称（从文件路径自动提取）
            tool_name: 工具函数名称（从服务名称自动生成）
            tool_param_name: 工具参数名称
            tool_param_type: 工具参数类型
            tool_return_type: 工具返回类型
            tool_description: 工具描述
            tool_code: 工具函数代码块
            service_port: 服务端口（默认随机）
            author: 作者
            
        Returns:
            是否生成成功
        """
        # 从输出路径提取服务名
        if not service_name:
            service_name = Path(output_path).stem
        
        # 生成工具名
        if not tool_name:
            tool_name = f"{service_name}_main"
        
        # 处理端口
        port_code = "random.randint(10001, 18000)" if service_port is None else str(service_port)
        
        # 生成模板内容
        template = self._create_template(
            service_name=service_name,
            tool_name=tool_name,
            tool_param_name=tool_param_name,
            tool_param_type=tool_param_type,
            tool_return_type=tool_return_type,
            tool_description=tool_description,
            tool_code=tool_code,
            port_code=port_code,
            author=author
        )
        
        try:
            # 确保输出目录存在
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"✅ MCP服务器生成成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return False
    
    def generate_content(
        self,
        service_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_param_name: str = "path",
        tool_param_type: str = "str",
        tool_return_type: str = "str",
        tool_description: str = "MCP工具",
        tool_code: str = "# TODO Implement code logic\n    output = \"...\"",
        service_port: Optional[int] = None,
        author: str = "开发者"
    ) -> str:
        """
        生成MCP服务器代码内容（不写入文件）
        
        Args:
            service_name: 服务名称
            tool_name: 工具函数名称（从服务名称自动生成）
            tool_param_name: 工具参数名称
            tool_param_type: 工具参数类型
            tool_return_type: 工具返回类型
            tool_description: 工具描述
            tool_code: 工具函数代码块
            service_port: 服务端口（默认随机）
            author: 作者
            
        Returns:
            生成的代码内容
        """
        # 生成工具名
        if not tool_name:
            tool_name = f"{service_name}_main" if service_name else "main_tool"
        
        # 处理端口
        port_code = "random.randint(10001, 18000)" if service_port is None else str(service_port)
        
        # 生成模板内容
        template = self._create_template(
            service_name=service_name or "mcp_service",
            tool_name=tool_name,
            tool_param_name=tool_param_name,
            tool_param_type=tool_param_type,
            tool_return_type=tool_return_type,
            tool_description=tool_description,
            tool_code=tool_code,
            port_code=port_code,
            author=author
        )
        
        return template
    
    def _create_template(
        self,
        service_name: str,
        tool_name: str,
        tool_param_name: str,
        tool_param_type: str,
        tool_return_type: str,
        tool_description: str,
        tool_code: str,
        port_code: str,
        author: str
    ) -> str:
        """
        创建MCP服务器模板内容
        
        Args:
            service_name: 服务名称
            tool_name: 工具名称
            tool_param_name: 工具参数名
            tool_param_type: 工具参数类型
            tool_return_type: 工具返回类型
            tool_description: 工具描述
            tool_code: 工具函数代码块
            port_code: 端口代码
            author: 作者
            
        Returns:
            模板内容
        """
        return f'''"""
MCP服务器模板 - 基于example.py格式创建MCP服务器
作者: {author}
服务名称: {service_name}
"""

import argparse
import logging
import uvicorn
import time
import random
from fastapi.responses import JSONResponse
from mcp.server import FastMCP, Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount

mcp = FastMCP("{service_name}")

logger = logging.getLogger(__name__)

# 确保 mcp 工具装饰器能正确处理异步函数
@mcp.tool()
async def {tool_name}({tool_param_name}: {tool_param_type}) -> {tool_return_type}:
    """
    {tool_description},
    :param {tool_param_name}: input {tool_param_name}
    :return: output result
    """
    {tool_code}

    return output

async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({{"status": "healthy", "timestamp": int(time.time())}}) 

def create_starlette_app(mcp_server: Server, *, debug: bool = False):
    """Create Starlette application that provides MCP service through SSE"""
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
    
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
            Route("/sse/health", endpoint=health_check, methods=["GET"])
        ],
    )    

if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    default_port = {port_code}
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument("--host", default="0.0.0.0", help="MCP server host")
    parser.add_argument("--port", default=default_port, type=int, help="MCP server port")
    args = parser.parse_args()
 
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
'''
    
    @staticmethod
    def to_class_name(name: str) -> str:
        """
        将文件名转换为类名（PascalCase）
        
        Args:
            name: 文件名
            
        Returns:
            类名
        """
        # 移除下划线和连字符，转换为PascalCase
        parts = re.split(r'[-_]', name)
        return ''.join(word.capitalize() for word in parts)
