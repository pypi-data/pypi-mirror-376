#!/usr/bin/env python3
"""
测试 Google Trends MCP 服务器
"""

import asyncio
import json
import sys
from io import StringIO

# 模拟 MCP 客户端测试
async def test_mcp_server():
    """测试MCP服务器的工具功能"""
    print("🚀 开始测试 Google Trends MCP 服务器...")
    
    # 导入服务器模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("google_trends_mcp", "google-trends-mcp.py")
    google_trends_mcp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(google_trends_mcp)
    
    server = google_trends_mcp.server
    
    print("✅ 服务器模块加载成功")
    
    # 测试工具列表
    try:
        tools = await google_trends_mcp.handle_list_tools()
        print(f"📋 可用工具数量: {len(tools)}")
        for tool in tools:
            print(f"   - 工具名: {tool.name}")
            print(f"   - 描述: {tool.description}")
        
        # 测试工具调用
        print("\n🔍 测试工具调用...")
        test_args = {
            "keywords": ["咖啡", "茶"],
            "timeframe": "today 1-m"
        }
        
        print(f"📊 测试参数: {test_args}")
        
        result = await google_trends_mcp.handle_call_tool("google_trends_analysis", test_args)
        
        print("✅ 工具调用成功!")
        print("📈 分析结果预览:")
        content = result[0].text
        # 只显示前300个字符
        preview = content[:300] + "..." if len(content) > 300 else content
        print(preview)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    if success:
        print("\n🎉 所有测试通过! MCP 服务器工作正常")
    else:
        print("\n💥 测试失败，请检查错误信息")
        sys.exit(1)
