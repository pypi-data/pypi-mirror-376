#!/usr/bin/env python3
"""
Google Trends MCP Server - 基本使用示例

这个示例展示了如何在 Python 中直接使用 MCP 服务器进行测试。
注意：在实际使用中，MCP 服务器应该通过 Agent 客户端调用。
"""

import asyncio
import json
from google_trends_mcp.server import server, handle_call_tool, handle_list_tools


async def basic_example():
    """基本使用示例"""
    print("🚀 Google Trends MCP Server - 基本使用示例")
    print("=" * 50)
    
    # 1. 列出可用工具
    print("\n📋 1. 获取可用工具列表")
    tools = await handle_list_tools()
    for tool in tools:
        print(f"   工具名: {tool.name}")
        print(f"   描述: {tool.description}")
    
    # 2. 分析单个关键词
    print("\n📊 2. 分析单个关键词 - iPhone")
    try:
        result = await handle_call_tool(
            "google_trends_analysis",
            {
                "keywords": ["iPhone"],
                "timeframe": "today 3-m"
            }
        )
        print("✅ 分析完成！")
        print("📈 结果预览:")
        preview = result[0].text[:300] + "..." if len(result[0].text) > 300 else result[0].text
        print(preview)
    except Exception as e:
        print(f"❌ 分析失败: {e}")
    
    # 3. 对比多个关键词
    print("\n🆚 3. 对比分析 - iPhone vs Android")
    try:
        result = await handle_call_tool(
            "google_trends_analysis",
            {
                "keywords": ["iPhone", "Android"],
                "timeframe": "today 6-m"
            }
        )
        print("✅ 对比分析完成！")
        print("📈 结果预览:")
        preview = result[0].text[:500] + "..." if len(result[0].text) > 500 else result[0].text
        print(preview)
    except Exception as e:
        print(f"❌ 对比分析失败: {e}")


async def market_research_example():
    """市场研究示例"""
    print("\n" + "=" * 50)
    print("🔍 市场研究示例 - 咖啡市场分析")
    print("=" * 50)
    
    coffee_keywords = ["咖啡", "星巴克", "瑞幸咖啡"]
    
    try:
        result = await handle_call_tool(
            "google_trends_analysis",
            {
                "keywords": coffee_keywords,
                "timeframe": "today 12-m"
            }
        )
        
        print("✅ 咖啡市场分析完成！")
        print("\n📊 完整分析报告:")
        print("-" * 50)
        print(result[0].text)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ 市场分析失败: {e}")
        print("💡 提示: 这可能是由于 Google Trends API 限制导致的")


async def trend_monitoring_example():
    """趋势监控示例"""
    print("\n" + "=" * 50)
    print("📈 趋势监控示例 - 科技产品趋势")
    print("=" * 50)
    
    tech_keywords = ["ChatGPT", "AI", "机器学习"]
    timeframes = ["today 3-m", "today 12-m"]
    
    for timeframe in timeframes:
        print(f"\n⏱️  时间范围: {timeframe}")
        try:
            result = await handle_call_tool(
                "google_trends_analysis",
                {
                    "keywords": tech_keywords,
                    "timeframe": timeframe
                }
            )
            
            # 提取关键信息
            content = result[0].text
            if "平均关注度对比" in content:
                lines = content.split('\n')
                for line in lines:
                    if '🥇' in line or '🥈' in line or '🥉' in line:
                        print(f"   {line.strip()}")
            
            # 添加延迟避免API限制
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ❌ 分析失败: {e}")


async def main():
    """主函数"""
    print("🌟 Google Trends MCP Server 示例程序")
    print("这些示例展示了如何使用 Google Trends 进行各种分析")
    
    try:
        # 运行基本示例
        await basic_example()
        
        # 等待一段时间避免API限制
        print("\n⏳ 等待 5 秒避免 API 限制...")
        await asyncio.sleep(5)
        
        # 运行市场研究示例
        await market_research_example()
        
        # 等待一段时间避免API限制
        print("\n⏳ 等待 5 秒避免 API 限制...")
        await asyncio.sleep(5)
        
        # 运行趋势监控示例
        await trend_monitoring_example()
        
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
    
    print("\n🎉 示例程序执行完成！")
    print("💡 在实际使用中，请将 MCP 服务器集成到 Agent 客户端中")


if __name__ == "__main__":
    asyncio.run(main())
