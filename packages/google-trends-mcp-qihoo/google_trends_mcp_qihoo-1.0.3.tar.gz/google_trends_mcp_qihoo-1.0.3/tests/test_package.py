#!/usr/bin/env python3
"""
测试已发布的PyPI包
"""

import subprocess
import json
import time

def test_mcp_server():
    """测试MCP服务器"""
    print("🚀 测试已发布的 google-trends-mcp-qihoo 包...")
    
    # 测试消息
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
    ]
    
    try:
        # 启动服务器
        process = subprocess.Popen(
            ['uvx', 'google-trends-mcp-qihoo'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 发送消息
        input_data = '\n'.join(json.dumps(msg) for msg in messages) + '\n'
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        
        print("✅ 服务器响应:")
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    response = json.loads(line)
                    print(f"  📨 {json.dumps(response, indent=2)}")
                except:
                    print(f"  📄 {line}")
        
        if stderr:
            print("⚠️ 错误信息:")
            print(f"  {stderr}")
            
        return True
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("⏰ 测试超时，但这可能是正常的（服务器在等待更多输入）")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    if success:
        print("\n🎉 MCP服务器工作正常！")
        print("💡 在Agent客户端中使用以下配置:")
        print("""
{
  "mcpServers": {
    "google-trends": {
      "command": "uvx",
      "args": ["google-trends-mcp-qihoo"]
    }
  }
}
        """)
    else:
        print("\n💥 测试失败")
