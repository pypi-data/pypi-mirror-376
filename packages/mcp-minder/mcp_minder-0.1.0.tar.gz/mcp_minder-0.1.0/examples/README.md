# MCP Minder Client Examples

这个目录包含了使用 MCP Minder 客户端库的示例代码。

## 安装

```bash
# 从 PyPI 安装
pip install mcp-minder

# 或者从源码安装
pip install -e .
```

## 基本使用

### 1. 创建客户端实例

```python
from mcp_generator.client import McpMinder

# 创建客户端实例
minder = McpMinder.get_service(
    url="http://localhost:8000",  # MCP Minder API 服务器地址
    servername="my_mcp_server"    # 要管理的 MCP 服务名称
)
```

### 2. 同步操作

```python
# 获取服务信息
info = minder.get_info_sync()
print(f"服务信息: {info}")

# 启动服务
result = minder.start_sync(port=8080)
print(f"启动结果: {result}")

# 检查状态
status = minder.get_status_sync()
print(f"服务状态: {status}")

# 获取日志
logs = minder.get_logs_sync(lines=10)
print(f"服务日志: {logs}")

# 停止服务
result = minder.stop_sync()
print(f"停止结果: {result}")
```

### 3. 异步操作

```python
import asyncio

async def manage_service():
    minder = McpMinder.get_service("http://localhost:8000", "my_mcp_server")
    
    # 获取服务信息
    info = await minder.get_info()
    print(f"服务信息: {info}")
    
    # 启动服务
    result = await minder.start(port=8080)
    print(f"启动结果: {result}")
    
    # 检查状态
    status = await minder.get_status()
    print(f"服务状态: {status}")
    
    # 停止服务
    result = await minder.stop()
    print(f"停止结果: {result}")

# 运行异步函数
asyncio.run(manage_service())
```

### 4. 使用上下文管理器

```python
# 同步上下文管理器
with McpMinder.get_service("http://localhost:8000", "my_mcp_server") as minder:
    info = minder.get_info_sync()
    result = minder.start_sync(port=8080)
    print(f"服务启动: {result}")

# 异步上下文管理器
async def use_context_manager():
    async with McpMinder.get_service("http://localhost:8000", "my_mcp_server") as minder:
        info = await minder.get_info()
        result = await minder.start(port=8080)
        print(f"服务启动: {result}")

asyncio.run(use_context_manager())
```

### 5. 列出所有服务

```python
# 列出服务器上的所有服务
minder = McpMinder.get_service("http://localhost:8000", "dummy")
services = minder.list_all_services_sync()

print(f"找到 {len(services)} 个服务:")
for service in services:
    print(f"  - {service.name}: {service.status} (端口: {service.port})")
```

### 6. 健康检查

```python
# 检查 MCP Minder 服务器是否健康
minder = McpMinder.get_service("http://localhost:8000", "dummy")

if minder.health_check_sync():
    print("✅ MCP Minder 服务器运行正常")
else:
    print("❌ MCP Minder 服务器不可用")
```

## 错误处理

```python
from mcp_generator.client import McpMinder, McpMinderError, McpMinderConnectionError

try:
    minder = McpMinder.get_service("http://localhost:8000", "my_server")
    result = minder.start_sync(port=8080)
    print(f"启动成功: {result}")
    
except McpMinderConnectionError as e:
    print(f"连接错误: {e}")
except McpMinderError as e:
    print(f"其他错误: {e}")
```

## 运行示例

```bash
# 运行完整示例
python examples/client_usage.py
```

## API 参考

### McpMinder 类

#### 类方法
- `get_service(url: str, servername: str, timeout: int = 30) -> McpMinder`

#### 实例方法

**同步方法:**
- `get_info_sync() -> ServiceInfo`
- `start_sync(port: Optional[int] = None) -> Dict[str, Any]`
- `stop_sync() -> Dict[str, Any]`
- `restart_sync(port: Optional[int] = None) -> Dict[str, Any]`
- `delete_sync() -> Dict[str, Any]`
- `get_logs_sync(lines: int = 50) -> str`
- `get_status_sync() -> str`
- `health_check_sync() -> bool`
- `list_all_services_sync() -> List[ServiceInfo]`

**异步方法:**
- `get_info() -> ServiceInfo`
- `start(port: Optional[int] = None) -> Dict[str, Any]`
- `stop() -> Dict[str, Any]`
- `restart(port: Optional[int] = None) -> Dict[str, Any]`
- `delete() -> Dict[str, Any]`
- `get_logs(lines: int = 50) -> str`
- `get_status() -> str`
- `health_check() -> bool`
- `list_all_services() -> List[ServiceInfo]`

### ServiceInfo 类

- `id: str` - 服务 ID
- `name: str` - 服务名称
- `file_path: str` - 服务文件路径
- `host: str` - 服务主机地址
- `port: int` - 服务端口
- `status: str` - 服务状态
- `pid: int` - 进程 ID
- `description: str` - 服务描述
- `author: str` - 服务作者
- `created_at: str` - 创建时间
- `updated_at: str` - 更新时间

### 异常类

- `McpMinderError` - 基础异常类
- `McpMinderConnectionError` - 连接错误
- `McpMinderAPIError` - API 错误
- `McpMinderServiceError` - 服务操作错误
