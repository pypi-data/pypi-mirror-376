#!/usr/bin/env python3
"""
快速功能测试

验证MCP Minder的核心功能是否正常工作
"""

import tempfile
from pathlib import Path
from mcp_generator import MCPGenerator, ServiceManager


def test_basic_functionality():
    """测试基本功能"""
    print("🧪 MCP Minder 快速功能测试")
    print("=" * 40)
    
    try:
        # 1. 测试生成器
        print("📝 测试MCP生成器...")
        generator = MCPGenerator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            output_path = f.name
        
        success = generator.generate(
            output_path=output_path,
            service_name="quick_test_service",
            tool_name="quick_test_tool",
            tool_description="快速测试工具"
        )
        
        if success and Path(output_path).exists():
            print("✅ MCP生成器功能正常")
        else:
            print("❌ MCP生成器功能异常")
            return False
        
        # 2. 测试服务管理器
        print("🔧 测试服务管理器...")
        service_manager = ServiceManager()
        
        service_id = service_manager.register_service(
            name="quick_test_service",
            file_path=output_path,
            port=8080,
            description="快速测试服务"
        )
        
        service_info = service_manager.get_service(service_id)
        if service_info and service_info.name == "quick_test_service":
            print("✅ 服务管理器功能正常")
        else:
            print("❌ 服务管理器功能异常")
            return False
        
        # 3. 测试服务列表
        print("📋 测试服务列表...")
        services = service_manager.list_services()
        if isinstance(services, list):
            print(f"✅ 服务列表功能正常，当前有 {len(services)} 个服务")
        else:
            print("❌ 服务列表功能异常")
            return False
        
        # 4. 清理
        print("🗑️ 清理测试数据...")
        service_manager.delete_service(service_id)
        Path(output_path).unlink(missing_ok=True)
        print("✅ 清理完成")
        
        print("\n🎉 所有核心功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_interface():
    """测试Web界面"""
    print("\n🌐 测试Web界面...")
    
    try:
        from mcp_generator.web.gradio_app import MCPMinderWebApp
        app = MCPMinderWebApp()
        print("✅ Web界面模块导入成功")
        
        # 测试生成功能
        result, code = app.generate_mcp_server(
            service_name="web_test_service",
            tool_name="web_test_tool",
            tool_param_name="input_data",
            tool_param_type="str",
            tool_return_type="str",
            tool_description="Web测试工具",
            service_port=8080,
            author="Web测试"
        )
        
        if "成功" in result:
            print("✅ Web界面生成功能正常")
        else:
            print(f"❌ Web界面生成功能异常: {result}")
            return False
        
        app.cleanup_temp_files()
        print("✅ Web界面功能正常")
        return True
        
    except Exception as e:
        print(f"❌ Web界面测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始MCP Minder功能验证")
    
    # 测试核心功能
    core_success = test_basic_functionality()
    
    # 测试Web界面
    web_success = test_web_interface()
    
    print("\n📊 测试结果汇总")
    print("=" * 40)
    print(f"核心功能: {'✅ 通过' if core_success else '❌ 失败'}")
    print(f"Web界面: {'✅ 通过' if web_success else '❌ 失败'}")
    
    if core_success and web_success:
        print("\n🎉 所有功能验证通过！MCP Minder可以正常使用。")
        print("\n💡 使用方式:")
        print("  1. 命令行生成: mcp-generator my_server.py")
        print("  2. Web界面: mcp-web")
        print("  3. API服务器: mcp-api-server")
        print("  4. 服务启动器: mcp-launcher")
        return True
    else:
        print("\n⚠️ 部分功能验证失败，请检查相关配置。")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        exit(1)
