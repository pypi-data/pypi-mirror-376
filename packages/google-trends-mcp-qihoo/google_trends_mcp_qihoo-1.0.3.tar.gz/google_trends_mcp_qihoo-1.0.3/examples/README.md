# 使用示例

这个目录包含了 Google Trends MCP Server 的各种使用示例。

## 📁 文件说明

### `claude_config.json`
Claude Desktop 的配置文件示例。将此配置添加到你的 Claude Desktop 配置文件中：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

### `basic_usage.py`
Python 脚本示例，展示如何直接调用 MCP 服务器的功能。包含：
- 获取工具列表
- 单个关键词分析
- 多关键词对比分析
- 市场研究案例
- 趋势监控案例

## 🚀 运行示例

### 1. 在 Claude Desktop 中使用

1. 将 `claude_config.json` 的内容添加到你的 Claude 配置文件中
2. 重启 Claude Desktop
3. 在对话中使用 Google Trends 分析功能

示例对话：
```
用户: 帮我分析一下 iPhone 和 Android 在过去 6 个月的搜索趋势

Claude: 我来帮你分析 iPhone 和 Android 的搜索趋势...
[调用 google_trends_analysis 工具]
```

### 2. 运行 Python 示例

```bash
# 确保已安装包
pip install google-trends-mcp-qihoo

# 运行示例
cd examples/
python basic_usage.py
```

## 📊 示例场景

### 市场研究
```python
# 分析咖啡市场
keywords = ["咖啡", "星巴克", "瑞幸咖啡"]
timeframe = "today 12-m"
```

### 竞品分析
```python
# 比较手机品牌
keywords = ["iPhone", "Samsung", "华为"]
timeframe = "today 6-m"
```

### 趋势监控
```python
# 监控科技趋势
keywords = ["ChatGPT", "AI", "机器学习"]
timeframe = "today 3-m"
```

### 内容策划
```python
# 分析热门话题
keywords = ["短视频", "直播", "元宇宙"]
timeframe = "today 12-m"
```

## 💡 使用技巧

1. **关键词选择**
   - 使用通用、热门的关键词
   - 避免过于具体或小众的词汇
   - 可以包含品牌名、产品名或概念

2. **时间范围**
   - `today 3-m`: 适合短期趋势分析
   - `today 12-m`: 适合年度趋势分析
   - `today 5-y`: 适合长期趋势分析

3. **API 限制**
   - Google Trends 有频率限制
   - 如遇到 429 错误，请稍后重试
   - 建议在请求间添加适当延迟

4. **结果解读**
   - 关注度分数是相对值，不是绝对值
   - 上升搜索词代表新的市场机会
   - 趋势变化百分比显示动态变化

## 🔧 自定义配置

你可以根据需要修改配置：

```json
{
  "mcpServers": {
    "google-trends": {
      "command": "uvx",
      "args": ["google-trends-mcp-qihoo"],
      "env": {
        "GOOGLE_TRENDS_TIMEOUT": "30"
      }
    }
  }
}
```

## ❓ 常见问题

**Q: 为什么有些关键词没有数据？**
A: 可能是因为关键词太小众或时间范围内搜索量不足。

**Q: 如何提高分析准确性？**
A: 使用更通用的关键词，选择合适的时间范围，多次验证结果。

**Q: 可以分析中文关键词吗？**
A: 可以，服务器已配置为中文语言环境。
