#!/usr/bin/env python3
"""
Google Trends MCP Server
用于分析Google搜索趋势的MCP服务器
"""

import asyncio
from typing import List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pytrends.request import TrendReq

# 初始化MCP服务器
server = Server("google-trends-tools", version="1.0.0")

# 全局pytrends实例
pytrends = None

def get_pytrends():
    """获取pytrends实例，延迟初始化避免启动时的网络问题"""
    global pytrends
    if pytrends is None:
        pytrends = TrendReq(hl='zh-CN', tz=360)
    return pytrends

# 定义工具
google_trends_tool = Tool(
    name="google_trends_analysis",
    description="获取Google Trends数据并提供分析报告",
    inputSchema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "关键词列表，例如 ['智能咖啡机', 'nespresso']"
            },
            "timeframe": {
                "type": "string",
                "description": "时间范围，默认为 'today 3-m' (最近3个月)",
                "default": "today 3-m"
            }
        },
        "required": ["keywords"]
    }
)

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """处理工具调用"""
    
    if name != "google_trends_analysis":
        raise ValueError(f"Unknown tool: {name}")
    
    keywords = arguments.get("keywords", [])
    timeframe = arguments.get("timeframe", "today 3-m")
    
    if not keywords:
        return [TextContent(type="text", text="❌ 错误：请提供至少一个关键词")]
    
    if len(keywords) > 5:
        return [TextContent(type="text", text="❌ 错误：最多支持5个关键词同时分析")]
    
    try:
        trends = get_pytrends()
        
        # 构建载荷并发送请求
        trends.build_payload(keywords, timeframe=timeframe)
        
        # 获取兴趣随时间变化数据
        interest_over_time_df = trends.interest_over_time()
        
        if interest_over_time_df.empty:
            result = f"📊 未找到关键词 {keywords} 在时间段 {timeframe} 的趋势数据。\n请尝试：\n- 使用更通用的关键词\n- 调整时间范围\n- 检查关键词拼写"
            return [TextContent(type="text", text=result)]
        
        # 获取相关查询数据
        try:
            related_queries_dict = trends.related_queries()
        except Exception as e:
            related_queries_dict = {}
            print(f"获取相关查询数据失败: {e}")
        
        # 开始构建分析报告
        analysis = f"# 📊 Google Trends 分析报告\n\n"
        analysis += f"**关键词**: {', '.join(keywords)}\n"
        analysis += f"**时间范围**: {timeframe}\n"
        analysis += f"**生成时间**: {interest_over_time_df.index[-1].strftime('%Y-%m-%d')}\n\n"
        
        # 1. 平均兴趣度分析
        analysis += "## 📈 平均关注度对比\n\n"
        mean_interest = interest_over_time_df.mean(numeric_only=True).sort_values(ascending=False)
        
        for i, (kw, score) in enumerate(mean_interest.items(), 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            analysis += f"{emoji} **{kw}**: {score:.1f}分\n"
        
        analysis += "\n"
        
        # 2. 趋势变化分析
        analysis += "## 📊 趋势变化分析\n\n"
        
        # 计算最近趋势（最后4周 vs 前4周的平均值）
        if len(interest_over_time_df) >= 8:
            recent_period = interest_over_time_df.tail(4).mean(numeric_only=True)
            earlier_period = interest_over_time_df.head(len(interest_over_time_df)-4).tail(4).mean(numeric_only=True)
            
            for kw in keywords:
                if kw in recent_period and kw in earlier_period:
                    change = ((recent_period[kw] - earlier_period[kw]) / max(earlier_period[kw], 1)) * 100
                    if change > 20:
                        trend_emoji = "📈🔥"
                        trend_text = "强劲上升"
                    elif change > 5:
                        trend_emoji = "📈"
                        trend_text = "稳步上升"
                    elif change < -20:
                        trend_emoji = "📉❄️"
                        trend_text = "明显下降"
                    elif change < -5:
                        trend_emoji = "📉"
                        trend_text = "轻微下降"
                    else:
                        trend_emoji = "➡️"
                        trend_text = "相对稳定"
                    
                    analysis += f"- **{kw}**: {trend_emoji} {trend_text} ({change:+.1f}%)\n"
        
        analysis += "\n"
        
        # 3. 上升相关查询分析
        analysis += "## 🚀 热门上升搜索词 (市场机会)\n\n"
        found_rising = False
        
        for kw in keywords:
            if (kw in related_queries_dict and 
                related_queries_dict[kw] and 
                'rising' in related_queries_dict[kw] and 
                related_queries_dict[kw]['rising'] is not None and 
                not related_queries_dict[kw]['rising'].empty):
                
                found_rising = True
                analysis += f"### 🔍 关于 '{kw}' 的上升搜索词:\n"
                
                rising_df = related_queries_dict[kw]['rising'].head(5)
                for _, row in rising_df.iterrows():
                    value = row['value']
                    if isinstance(value, str) and value == 'Breakout':
                        growth = "🚀 爆发式增长"
                    elif isinstance(value, (int, float)):
                        growth = f"📈 +{value}%"
                    else:
                        growth = "📊 显著增长"
                    
                    analysis += f"- **{row['query']}** {growth}\n"
                analysis += "\n"
        
        if not found_rising:
            analysis += "暂无显著的上升搜索词数据。\n\n"
        
        # 4. 策略建议
        analysis += "## 💡 基于数据的策略建议\n\n"
        
        top_keyword = mean_interest.index[0]
        analysis += f"### 🎯 核心关键词策略\n"
        analysis += f"- **主推关键词**: '{top_keyword}' (平均关注度最高: {mean_interest[top_keyword]:.1f}分)\n"
        analysis += f"- 建议将此关键词作为核心投放和SEO优化重点\n\n"
        
        if found_rising:
            analysis += f"### 🌟 新兴机会点\n"
            analysis += f"- 关注上述'上升搜索词'，它们代表新的市场需求\n"
            analysis += f"- 可用于内容创作、长尾关键词优化和新产品开发方向\n\n"
        
        analysis += f"### 📅 时机建议\n"
        analysis += f"- 根据趋势变化，在关注度上升期加大营销投入\n"
        analysis += f"- 持续监控趋势变化，及时调整策略\n"
        
        return [TextContent(type="text", text=analysis)]
        
    except Exception as e:
        error_msg = f"❌ 获取Google Trends数据时发生错误: {str(e)}\n\n"
        error_msg += "可能的解决方案:\n"
        error_msg += "- 检查网络连接\n"
        error_msg += "- 稍后重试（可能是API限流）\n"
        error_msg += "- 尝试使用更通用的关键词\n"
        error_msg += "- 调整时间范围参数"
        return [TextContent(type="text", text=error_msg)]

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [google_trends_tool]

async def async_main():
    """启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def main():
    """命令行入口点"""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
