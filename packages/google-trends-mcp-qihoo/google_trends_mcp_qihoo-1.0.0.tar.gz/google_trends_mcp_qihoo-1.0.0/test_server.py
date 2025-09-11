#!/usr/bin/env python3
"""测试 Google Trends MCP 服务器"""

import asyncio
import json
import sys
import sys
sys.path.append('.')
import importlib.util
spec = importlib.util.spec_from_file_location("google_trends_mcp", "google-trends-mcp.py")
google_trends_mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_trends_mcp)
server = google_trends_mcp.server

async def test_server():
    """测试服务器功能"""
    print("🚀 启动 Google Trends MCP 服务器测试...")
    
    # 测试工具列表
    tools = await server.request_handlers["tools/list"](None)
    print(f"✅ 可用工具: {[tool.name for tool in tools]}")
    
    # 测试工具调用
    test_args = {
        "keywords": ["iPhone", "Android"],
        "timeframe": "today 3-m"
    }
    
    print(f"📊 测试关键词分析: {test_args}")
    
    try:
        result = await server.request_handlers["tools/call"]({
            "name": "google_trends_analysis",
            "arguments": test_args
        })
        
        print("✅ 分析结果:")
        print(result.content[0].text[:500] + "..." if len(result.content[0].text) > 500 else result.content[0].text)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_server())
