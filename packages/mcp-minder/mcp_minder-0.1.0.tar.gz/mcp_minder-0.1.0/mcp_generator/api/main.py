"""
MCP Minder FastAPI 应用

提供 RESTful API 接口用于远程管理 MCP 服务
"""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_generator.core.service_manager import ServiceManager
from mcp_generator.core.generator import MCPGenerator
from mcp_generator.api.models import (
    ServiceCreateRequest,
    ServiceUpdateRequest,
    ServiceStartRequest,
    ServiceListResponse,
    ServiceResponse,
    ServiceActionResponse,
    LogsResponse,
    MCPGenerateRequest,
    MCPGenerateResponse,
    HealthResponse,
    ServiceInfo
)

# 创建 FastAPI 应用
app = FastAPI(
    title="MCP Minder API",
    description="MCP服务器管理框架的RESTful API接口",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务管理器和生成器
service_manager = ServiceManager()
generator = MCPGenerator()


@app.get("/", response_model=HealthResponse)
async def root():
    """根路径健康检查"""
    services = service_manager.list_services()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        services_count=len(services)
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    services = service_manager.list_services()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        services_count=len(services)
    )


# ==================== 服务管理 API ====================

@app.post("/api/services", response_model=ServiceResponse)
async def create_service(request: ServiceCreateRequest):
    """创建新服务"""
    try:
        service_id = service_manager.register_service(
            name=request.name,
            file_path=request.file_path,
            host=request.host,
            description=request.description,
            author=request.author
        )
        
        service_info = service_manager.get_service(service_id)
        return ServiceResponse(
            success=True,
            service=ServiceInfo(**service_info.__dict__),
            message=f"服务 {request.name} 创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services", response_model=ServiceListResponse)
async def list_services(status: Optional[str] = Query(None, description="状态过滤器")):
    """获取服务列表"""
    try:
        services = service_manager.list_services(status_filter=status)
        service_infos = [ServiceInfo(**service.__dict__) for service in services]
        
        return ServiceListResponse(
            success=True,
            services=service_infos,
            total=len(service_infos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str):
    """获取特定服务信息"""
    try:
        service_info = service_manager.get_service(service_id)
        if not service_info:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        return ServiceResponse(
            success=True,
            service=ServiceInfo(**service_info.__dict__)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/by-name/{service_name}", response_model=ServiceResponse)
async def get_service_by_name(service_name: str):
    """根据服务名称获取服务信息"""
    try:
        service_info = service_manager.get_service_by_name(service_name)
        if not service_info:
            raise HTTPException(status_code=404, detail=f"服务 {service_name} 不存在")
        
        return ServiceResponse(
            success=True,
            service=ServiceInfo(**service_info.__dict__)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, request: ServiceUpdateRequest):
    """更新服务信息"""
    try:
        result = service_manager.update_service(
            service_id=service_id,
            name=request.name,
            port=request.port,
            host=request.host,
            description=request.description
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        service_info = service_manager.get_service(service_id)
        return ServiceResponse(
            success=True,
            service=ServiceInfo(**service_info.__dict__),
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/services/by-name/{service_name}", response_model=ServiceResponse)
async def update_service_by_name(service_name: str, request: ServiceUpdateRequest):
    """根据服务名称更新服务信息"""
    try:
        # 先获取服务ID
        service_id = service_manager.get_service_id_by_name(service_name)
        if not service_id:
            raise HTTPException(status_code=404, detail=f"服务 {service_name} 不存在")
        
        result = service_manager.update_service(
            service_id=service_id,
            name=request.name,
            port=request.port,
            host=request.host,
            description=request.description
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        service_info = service_manager.get_service(service_id)
        return ServiceResponse(
            success=True,
            service=ServiceInfo(**service_info.__dict__),
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/services/{service_id}", response_model=ServiceActionResponse)
async def delete_service(service_id: str):
    """删除服务"""
    try:
        result = service_manager.delete_service(service_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=service_id,
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/services/by-name/{service_name}", response_model=ServiceActionResponse)
async def delete_service_by_name(service_name: str):
    """根据服务名称删除服务"""
    try:
        result = service_manager.delete_service_by_name(service_name)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=result.get('service_id'),
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/{service_id}/start", response_model=ServiceActionResponse)
async def start_service(service_id: str, request: ServiceStartRequest = ServiceStartRequest()):
    """启动服务"""
    try:
        result = service_manager.start_service(service_id, request.port)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=service_id,
            message=result['message'],
            pid=result.get('pid')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/by-name/{service_name}/start", response_model=ServiceActionResponse)
async def start_service_by_name(service_name: str, request: ServiceStartRequest = ServiceStartRequest()):
    """根据服务名称启动服务"""
    try:
        result = service_manager.start_service_by_name(service_name, request.port)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=result.get('service_id'),
            message=result['message'],
            pid=result.get('pid')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/{service_id}/stop", response_model=ServiceActionResponse)
async def stop_service(service_id: str):
    """停止服务"""
    try:
        result = service_manager.stop_service(service_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=service_id,
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/by-name/{service_name}/stop", response_model=ServiceActionResponse)
async def stop_service_by_name(service_name: str):
    """根据服务名称停止服务"""
    try:
        result = service_manager.stop_service_by_name(service_name)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ServiceActionResponse(
            success=True,
            service_id=result.get('service_id'),
            message=result['message']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/by-name/{service_name}/restart", response_model=ServiceActionResponse)
async def restart_service_by_name(service_name: str):
    """根据服务名称重启服务"""
    try:
        # 先停止服务
        stop_result = service_manager.stop_service_by_name(service_name)
        if not stop_result['success']:
            raise HTTPException(status_code=400, detail=f"停止服务失败: {stop_result['error']}")
        
        # 等待一秒
        import asyncio
        await asyncio.sleep(1)
        
        # 再启动服务
        start_result = service_manager.start_service_by_name(service_name)
        if not start_result['success']:
            raise HTTPException(status_code=400, detail=f"启动服务失败: {start_result['error']}")
        
        return ServiceActionResponse(
            success=True,
            service_id=start_result.get('service_id'),
            message=f"服务 {service_name} 重启成功",
            pid=start_result.get('pid')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/{service_id}/logs", response_model=LogsResponse)
async def get_service_logs(
    service_id: str,
    lines: int = Query(50, description="返回的日志行数")
):
    """获取服务日志"""
    try:
        result = service_manager.get_service_logs(service_id, lines)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return LogsResponse(
            success=True,
            logs=result['logs'],
            total_lines=result['total_lines'],
            returned_lines=result['returned_lines']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/by-name/{service_name}/logs", response_model=LogsResponse)
async def get_service_logs_by_name(
    service_name: str,
    lines: int = Query(50, description="返回的日志行数")
):
    """根据服务名称获取服务日志"""
    try:
        result = service_manager.get_service_logs_by_name(service_name, lines)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return LogsResponse(
            success=True,
            logs=result['logs'],
            total_lines=result['total_lines'],
            returned_lines=result['returned_lines']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/sync", response_model=ServiceActionResponse)
async def sync_service_status():
    """同步服务状态"""
    try:
        service_manager.sync_service_status()
        return ServiceActionResponse(
            success=True,
            message="服务状态同步完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/sync-services", response_model=ServiceActionResponse)
async def sync_services():
    """同步服务列表（重新扫描mcpserver目录）"""
    try:
        service_manager.sync_services()
        return ServiceActionResponse(
            success=True,
            message="服务列表同步完成"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MCP 生成器 API ====================

@app.post("/api/generate", response_model=MCPGenerateResponse)
async def generate_mcp_server(request: MCPGenerateRequest):
    """生成 MCP 服务器文件"""
    try:
        success = generator.generate(
            output_path=request.output_path,
            service_name=request.service_name,
            tool_name=request.tool_name,
            tool_param_name=request.tool_param_name,
            tool_param_type=request.tool_param_type,
            tool_return_type=request.tool_return_type,
            tool_description=request.tool_description,
            tool_code=request.tool_code,
            service_port=request.service_port,
            author=request.author
        )
        
        if success:
            return MCPGenerateResponse(
                success=True,
                output_path=request.output_path,
                message=f"MCP服务器文件生成成功: {request.output_path}"
            )
        else:
            raise HTTPException(status_code=500, detail="MCP服务器文件生成失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preview")
async def preview_mcp_server(request: MCPGenerateRequest):
    """预览MCP服务器代码（不生成文件）"""
    try:
        content = generator.generate_content(
            service_name=request.service_name,
            tool_name=request.tool_name,
            tool_param_name=request.tool_param_name,
            tool_param_type=request.tool_param_type,
            tool_return_type=request.tool_return_type,
            tool_description=request.tool_description,
            tool_code=request.tool_code,
            service_port=request.service_port,
            author=request.author
        )
        
        return {
            "success": True,
            "content": content,
            "message": "MCP服务器代码预览生成成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 批量操作 API ====================

@app.post("/api/services/start-all", response_model=ServiceActionResponse)
async def start_all_services():
    """启动所有停止的服务"""
    try:
        services = service_manager.list_services(status_filter="stopped")
        started_count = 0
        failed_count = 0
        
        for service in services:
            result = service_manager.start_service(service.id)
            if result['success']:
                started_count += 1
            else:
                failed_count += 1
        
        return ServiceActionResponse(
            success=failed_count == 0,
            message=f"批量启动完成: 成功 {started_count} 个，失败 {failed_count} 个"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/stop-all", response_model=ServiceActionResponse)
async def stop_all_services():
    """停止所有运行中的服务"""
    try:
        services = service_manager.list_services(status_filter="running")
        stopped_count = 0
        failed_count = 0
        
        for service in services:
            result = service_manager.stop_service(service.id)
            if result['success']:
                stopped_count += 1
            else:
                failed_count += 1
        
        return ServiceActionResponse(
            success=failed_count == 0,
            message=f"批量停止完成: 成功 {stopped_count} 个，失败 {failed_count} 个"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/restart-all", response_model=ServiceActionResponse)
async def restart_all_services():
    """重启所有运行中的服务"""
    try:
        services = service_manager.list_services(status_filter="running")
        restarted_count = 0
        failed_count = 0
        
        for service in services:
            # 先停止
            stop_result = service_manager.stop_service(service.id)
            if stop_result['success']:
                # 等待一秒
                import asyncio
                await asyncio.sleep(1)
                # 再启动
                start_result = service_manager.start_service(service.id)
                if start_result['success']:
                    restarted_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        
        return ServiceActionResponse(
            success=failed_count == 0,
            message=f"批量重启完成: 成功 {restarted_count} 个，失败 {failed_count} 个"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 错误处理 ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404错误处理"""
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "资源不存在"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500错误处理"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "内部服务器错误"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
