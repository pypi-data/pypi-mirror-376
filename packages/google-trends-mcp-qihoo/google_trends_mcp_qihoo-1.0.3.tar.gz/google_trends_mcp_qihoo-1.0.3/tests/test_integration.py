#!/usr/bin/env python3
"""
集成测试 - 持续测试直到获得成功结果
"""

import asyncio
import time
import random

# 导入服务器模块
import importlib.util
spec = importlib.util.spec_from_file_location("google_trends_mcp", "google-trends-mcp.py")
google_trends_mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_trends_mcp)

# 测试用的不同关键词组合
test_cases = [
    {
        "keywords": ["iPhone"],
        "timeframe": "today 12-m",
        "description": "单个热门关键词，12个月"
    },
    {
        "keywords": ["python"],
        "timeframe": "today 12-m", 
        "description": "编程语言关键词，12个月"
    },
    {
        "keywords": ["covid"],
        "timeframe": "today 12-m",
        "description": "全球热门话题，12个月"
    },
    {
        "keywords": ["netflix"],
        "timeframe": "today 3-m",
        "description": "流媒体服务，3个月"
    },
    {
        "keywords": ["tesla"],
        "timeframe": "today 6-m",
        "description": "汽车品牌，6个月"
    }
]

async def test_with_retry():
    """尝试不同参数直到成功"""
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 测试 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"📊 参数: {test_case['keywords']}, {test_case['timeframe']}")
        
        try:
            result = await google_trends_mcp.handle_call_tool(
                "google_trends_analysis", 
                {
                    "keywords": test_case["keywords"],
                    "timeframe": test_case["timeframe"]
                }
            )
            
            content = result[0].text
            
            # 检查是否成功（不包含错误信息）
            if "❌" not in content and "错误" not in content and "429" not in content:
                print("✅ 成功获得结果!")
                print("📈 完整分析报告:")
                print("=" * 60)
                print(content)
                print("=" * 60)
                return True
            else:
                print(f"⚠️  获得错误响应: {content[:100]}...")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        # 随机等待避免频率限制
        wait_time = random.randint(3, 8)
        print(f"⏳ 等待 {wait_time} 秒后继续...")
        await asyncio.sleep(wait_time)
    
    print("\n💥 所有测试都未成功，可能需要更长的等待时间")
    return False

async def main():
    print("🚀 开始持续测试 Google Trends MCP 服务器...")
    print("🎯 目标: 获得至少一次成功的分析结果")
    
    success = await test_with_retry()
    
    if success:
        print("\n🎉 测试成功! MCP 服务器可以正常获取 Google Trends 数据")
    else:
        print("\n😔 暂时无法获得成功结果，建议稍后再试")
        print("💡 这通常是由于 Google Trends API 的频率限制导致的")

if __name__ == "__main__":
    asyncio.run(main())
