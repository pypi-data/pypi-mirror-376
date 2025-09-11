#!/usr/bin/env python3
"""
单元测试 - Google Trends MCP Server
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from google_trends_mcp.server import (
    server, 
    handle_call_tool, 
    handle_list_tools, 
    get_pytrends,
    google_trends_tool
)


class TestGoogleTrendsMCPServer:
    """Google Trends MCP Server 测试类"""
    
    def test_server_initialization(self):
        """测试服务器初始化"""
        assert server.name == "google-trends-tools"
        assert server.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """测试工具列表"""
        tools = await handle_list_tools()
        assert len(tools) == 1
        assert tools[0].name == "google_trends_analysis"
        assert "Google Trends" in tools[0].description
    
    def test_tool_definition(self):
        """测试工具定义"""
        tool = google_trends_tool
        assert tool.name == "google_trends_analysis"
        assert tool.inputSchema["type"] == "object"
        assert "keywords" in tool.inputSchema["properties"]
        assert "timeframe" in tool.inputSchema["properties"]
        assert "keywords" in tool.inputSchema["required"]
    
    @pytest.mark.asyncio
    async def test_call_tool_invalid_name(self):
        """测试调用无效工具名"""
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_call_tool("invalid_tool", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_no_keywords(self):
        """测试无关键词调用"""
        result = await handle_call_tool("google_trends_analysis", {})
        assert len(result) == 1
        assert "错误" in result[0].text
        assert "请提供至少一个关键词" in result[0].text
    
    @pytest.mark.asyncio
    async def test_call_tool_too_many_keywords(self):
        """测试关键词过多"""
        keywords = ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"]
        result = await handle_call_tool("google_trends_analysis", {"keywords": keywords})
        assert len(result) == 1
        assert "错误" in result[0].text
        assert "最多支持5个关键词" in result[0].text
    
    def test_get_pytrends(self):
        """测试pytrends实例获取"""
        # 重置全局变量
        import google_trends_mcp.server as server_module
        server_module.pytrends = None
        
        trends = get_pytrends()
        assert trends is not None
        
        # 测试单例模式
        trends2 = get_pytrends()
        assert trends is trends2


class TestGoogleTrendsIntegration:
    """Google Trends API 集成测试"""
    
    @pytest.mark.asyncio
    @patch('google_trends_mcp.server.get_pytrends')
    async def test_successful_analysis(self, mock_get_pytrends):
        """测试成功的分析流程（模拟）"""
        # 模拟 pytrends 对象
        mock_trends = Mock()
        mock_get_pytrends.return_value = mock_trends
        
        # 模拟数据
        import pandas as pd
        mock_df = pd.DataFrame({
            'iPhone': [50, 60, 70],
            'isPartial': [False, False, False]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        
        mock_trends.build_payload.return_value = None
        mock_trends.interest_over_time.return_value = mock_df
        mock_trends.related_queries.return_value = {'iPhone': {'rising': None}}
        
        result = await handle_call_tool(
            "google_trends_analysis", 
            {"keywords": ["iPhone"], "timeframe": "today 3-m"}
        )
        
        assert len(result) == 1
        assert "Google Trends 分析报告" in result[0].text
        assert "iPhone" in result[0].text
        assert "平均关注度对比" in result[0].text
    
    @pytest.mark.asyncio
    @patch('google_trends_mcp.server.get_pytrends')
    async def test_empty_data_response(self, mock_get_pytrends):
        """测试空数据响应"""
        mock_trends = Mock()
        mock_get_pytrends.return_value = mock_trends
        
        # 模拟空数据
        import pandas as pd
        mock_df = pd.DataFrame()
        
        mock_trends.build_payload.return_value = None
        mock_trends.interest_over_time.return_value = mock_df
        
        result = await handle_call_tool(
            "google_trends_analysis", 
            {"keywords": ["very_rare_keyword"], "timeframe": "today 3-m"}
        )
        
        assert len(result) == 1
        assert "未找到关键词" in result[0].text
        assert "趋势数据" in result[0].text
    
    @pytest.mark.asyncio
    @patch('google_trends_mcp.server.get_pytrends')
    async def test_api_error_handling(self, mock_get_pytrends):
        """测试API错误处理"""
        mock_trends = Mock()
        mock_get_pytrends.return_value = mock_trends
        
        # 模拟API错误
        mock_trends.build_payload.side_effect = Exception("API Error")
        
        result = await handle_call_tool(
            "google_trends_analysis", 
            {"keywords": ["test"], "timeframe": "today 3-m"}
        )
        
        assert len(result) == 1
        assert "获取Google Trends数据时发生错误" in result[0].text
        assert "可能的解决方案" in result[0].text


class TestParameterValidation:
    """参数验证测试"""
    
    @pytest.mark.asyncio
    async def test_valid_timeframes(self):
        """测试有效的时间范围"""
        valid_timeframes = [
            "today 3-m",
            "today 12-m", 
            "today 5-y",
            "all"
        ]
        
        for timeframe in valid_timeframes:
            # 这里只测试参数不会导致立即错误
            # 实际API调用在集成测试中处理
            try:
                result = await handle_call_tool(
                    "google_trends_analysis", 
                    {"keywords": ["test"], "timeframe": timeframe}
                )
                # 应该返回结果（可能是错误，但不是参数错误）
                assert len(result) == 1
            except ValueError as e:
                # 不应该有参数验证错误
                if "timeframe" in str(e):
                    pytest.fail(f"Timeframe {timeframe} should be valid")
    
    @pytest.mark.asyncio
    async def test_keyword_types(self):
        """测试关键词类型"""
        # 测试字符串列表
        result = await handle_call_tool(
            "google_trends_analysis", 
            {"keywords": ["test1", "test2"]}
        )
        assert len(result) == 1
        
        # 测试空列表
        result = await handle_call_tool(
            "google_trends_analysis", 
            {"keywords": []}
        )
        assert len(result) == 1
        assert "错误" in result[0].text


if __name__ == "__main__":
    pytest.main([__file__])
