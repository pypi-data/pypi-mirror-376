#!/usr/bin/env python3
"""
启动 Google Trends MCP 服务器的包装脚本
"""

import asyncio
import sys
import signal

# 导入我们的MCP服务器
import importlib.util
spec = importlib.util.spec_from_file_location("google_trends_mcp", "google-trends-mcp.py")
google_trends_mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_trends_mcp)

def signal_handler(signum, frame):
    print("\n🛑 收到停止信号，正在关闭服务器...")
    sys.exit(0)

async def main():
    print("🚀 启动 Google Trends MCP 服务器...")
    print("📡 服务器正在监听 stdin/stdout...")
    print("💡 在 agent 客户端中使用此服务器来分析 Google 搜索趋势")
    print("⚠️  注意: Google Trends API 有频率限制，请适度使用")
    print("🔧 按 Ctrl+C 停止服务器\n")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务器
    await google_trends_mcp.main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
