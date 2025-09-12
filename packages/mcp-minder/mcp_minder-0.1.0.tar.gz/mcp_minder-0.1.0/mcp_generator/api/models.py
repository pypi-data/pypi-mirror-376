"""
API 数据模型

定义 FastAPI 请求和响应的数据模型
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class ServiceCreateRequest(BaseModel):
    """创建服务请求模型"""
    name: str = Field(..., description="服务名称")
    file_path: str = Field(..., description="服务文件路径")
    port: Optional[int] = Field(None, description="服务端口")
    host: str = Field("0.0.0.0", description="服务主机")
    description: Optional[str] = Field(None, description="服务描述")
    author: Optional[str] = Field(None, description="作者")


class ServiceUpdateRequest(BaseModel):
    """更新服务请求模型"""
    name: Optional[str] = Field(None, description="服务名称")
    port: Optional[int] = Field(None, description="服务端口")
    host: Optional[str] = Field(None, description="服务主机")
    description: Optional[str] = Field(None, description="服务描述")


class ServiceInfo(BaseModel):
    """服务信息响应模型"""
    id: str
    name: str
    file_path: str
    port: Optional[int]
    host: str
    status: str
    created_at: str
    updated_at: str
    pid: Optional[int] = None
    log_file: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None


class ServiceListResponse(BaseModel):
    """服务列表响应模型"""
    success: bool
    services: List[ServiceInfo]
    total: int


class ServiceResponse(BaseModel):
    """单个服务响应模型"""
    success: bool
    service: Optional[ServiceInfo] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ServiceStartRequest(BaseModel):
    """启动服务请求模型"""
    port: Optional[int] = Field(None, description="服务端口（可选，如果不指定则使用随机端口）")


class ServiceActionResponse(BaseModel):
    """服务操作响应模型"""
    success: bool
    service_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    pid: Optional[int] = None


class LogsResponse(BaseModel):
    """日志响应模型"""
    success: bool
    logs: Optional[str] = None
    total_lines: Optional[int] = None
    returned_lines: Optional[int] = None
    error: Optional[str] = None


class MCPGenerateRequest(BaseModel):
    """MCP服务器生成请求模型"""
    output_path: str = Field(..., description="输出文件路径")
    service_name: Optional[str] = Field(None, description="服务名称")
    tool_name: Optional[str] = Field(None, description="工具函数名称")
    tool_param_name: str = Field("path", description="工具参数名称")
    tool_param_type: str = Field("str", description="工具参数类型")
    tool_return_type: str = Field("str", description="工具返回类型")
    tool_description: str = Field("MCP工具", description="工具描述")
    tool_code: str = Field("# TODO Implement code logic\n    output = \"...\"", description="工具函数代码块")
    service_port: Optional[int] = Field(None, description="服务端口")
    author: str = Field("开发者", description="作者")


class MCPGenerateResponse(BaseModel):
    """MCP服务器生成响应模型"""
    success: bool
    output_path: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    version: str
    services_count: int
