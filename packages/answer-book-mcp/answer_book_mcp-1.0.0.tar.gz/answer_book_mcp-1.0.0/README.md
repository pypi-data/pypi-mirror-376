# 答案之书 MCP 服务

一个基于Model Context Protocol的智慧答案生成服务，为你的问题提供随机而富有哲理的答案。

## 功能特点

- 🎯 随机生成智慧答案
- 📊 查询历史记录和统计
- 🎨 支持自定义答案
- 💾 持久化存储配置

## 安装和使用

1. 安装依赖：`pip install -r requirements.txt`
2. 运行服务：`python answer_book_mcp.py`
3. 通过MCP客户端连接使用

## API说明

- `ask_question(question: str)` - 提问获取答案
- `get_recent_history(limit: int)` - 获取历史记录
- `get_statistics()` - 获取使用统计
- `add_custom_answer(answer_text: str)` - 添加自定义答案

## 使用示例
这个MCP服务可以通过各种MCP客户端使用，比如Claude、Cursor等：

```python
# 示例对话
用户：我应该接受这个工作机会吗？
答案之书：跟随你内心的声音。

用户：这个项目能成功吗？
答案之书：风险太大，建议谨慎。

用户：查看我的历史记录
答案之书：显示最近5条提问记录
```
