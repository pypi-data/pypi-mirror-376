"""
MCP服务器模板 - 基于example.py格式创建MCP服务器
作者: 开发者
服务名称: my_service
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

mcp = FastMCP("my_service")

logger = logging.getLogger(__name__)

# 确保 mcp 工具装饰器能正确处理异步函数
@mcp.tool()
async def my_tool(input_data: str) -> str:
    """
    这是一个MCP工具,
    :param input_data: input input_data
    :return: output result
    """
    # TODO Implement code logic
    output = "..."

    return output

async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "timestamp": int(time.time())}) 

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

    default_port = 0
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument("--host", default="0.0.0.0", help="MCP server host")
    parser.add_argument("--port", default=default_port, type=int, help="MCP server port")
    args = parser.parse_args()
 
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
