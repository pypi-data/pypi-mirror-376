from mcp.server import Server
from mcp.tools import Tool
from pytrends.request import TrendReq
import asyncio
from typing import Any
# 初始化MCP服务器和pytrends客户端
server = Server("google-trends-tools")
pytrends = TrendReq(hl='zh-CN', tz=360) # 设置为中文语言和东八区
@server.tool()
async def google_trends_analysis(keywords: list[str], timeframe: str = 'today 3-m') -> str:
    """
    Fetches Google Trends data for a list of keywords and provides an analysis.
    Perfect for identifying market trends and consumer interest over time.
    Args:
        keywords: A list of keywords to search for (e.g., ['智能咖啡机', 'nespresso']).
        timeframe: The time range for the trends data. Defaults to 'today 3-m' (last 3 months).
                   Other examples: 'today 12-m' (last year), 'all' (all time).
    """
    try:
        # 构建载荷并发送请求
        pytrends.build_payload(keywords, timeframe=timeframe)
        
        # 获取兴趣随时间变化数据
        interest_over_time_df = pytrends.interest_over_time()
        
        if interest_over_time_df.empty:
            return "No trends data found for the given keywords and timeframe."
        
        # 获取相关查询（上升趋势的查询）
        related_queries_dict = pytrends.related_queries()
        
        # 开始分析（这里可以极大地丰富）
        analysis = f"## Google Trends 分析报告 for '{', '.join(keywords)}' ({timeframe})\n\n"
        
        # 1. 计算平均兴趣度并比较
        mean_interest = interest_over_time_df.mean(numeric_only=True)
        analysis += "**平均关注度对比:**\n"
        for kw, score in mean_interest.items():
            analysis += f"- {kw}: {score:.2f}\n"
        analysis += "\n"
        
        # 2. 指出趋势（简单版：比较最近一周和最早一周）
        # ... (这里可以加入更复杂的时间序列分析)
        
        # 3. 分析相关上升查询（非常有价值！）
        analysis += "**近期上升的相关搜索词（市场机会点）:**\n"
        for kw in keywords:
            rising = related_queries_dict[kw]['rising']
            if rising is not None and not rising.empty:
                analysis += f"- 关于 '{kw}':\n"
                for _, row in rising.head(5).iterrows(): # 取前5个上升最快的词
                    analysis += f"  - '{row['query']}' (搜索增长率: {row['value']})\n"
        analysis += "\n"
        # 4. 给出策略建议
        analysis += "**基于趋势的初步营销建议:**\n"
        top_keyword = mean_interest.idxmax()
        analysis += f"- 关键词 '{top_keyword}' 的总体关注度最高，可考虑作为核心投放词。\n"
        analysis += "- 关注上述『上升相关搜索词』，它们代表了新的市场需求，可用于内容创作和SEO。\n"
        analysis += "- 结合时间序列数据，规划在关注度上升期加大广告投放力度。\n"
        return analysis
    except Exception as e:
        return f"An error occurred while fetching Google Trends data: {str(e)}"
# 运行服务器
if __name__ == "__main__":
    asyncio.run(server.run_standalone())