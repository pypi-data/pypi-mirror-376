# answer_book_mcp.py
from mcp.server.fastmcp import FastMCP
import random
import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Set
import logging
from pathlib import Path

# 配置日志 - 将输出重定向到stderr以避免干扰MCP JSON通信
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger("answer-book")

# 初始化MCP服务器
mcp = FastMCP("AnswerBook")

# 基础答案库 - 定义为常量
BASE_ANSWERS = [
    "是的，毫无疑问。",
    "时机未到，请耐心等待。",
    "跟随你内心的声音。",
    "风险太大，建议谨慎。",
    "这是一个很好的机会。",
    "重新考虑你的选择。",
    "答案就在你心中。",
    "外界因素会影响结果。",
    "保持乐观的态度。",
    "需要更多的信息。",
    "信任你的直觉。",
    "暂时搁置，稍后再议。",
    "与他人合作会有帮助。",
    "独自思考会更好。",
    "改变你的视角。",
    "答案是肯定的。",
    "答案是否定的。",
    "可能不会如你所愿。",
    "超出预期的好结果。",
    "顺其自然。",
    "主动出击。",
    "静观其变。",
    "需要做出牺牲。",
    "值得冒险一试。",
    "保持现状。",
    "寻求他人的建议。",
    "相信自己。",
    "命运掌握在自己手中。",
    "一切都是最好的安排。",
    "放下执念。"
]

class AnswerBook:
    def __init__(self):
        self.answers = self._load_answers()
        self.history = []
        self.stats = {"total_queries": 0, "popular_questions": {}}
        self._base_answers_set = set(BASE_ANSWERS)  # 用于快速查找基础答案
    
    def _get_config_dir(self) -> Path:
        """获取配置目录路径"""
        return Path.home()
    
    def _get_custom_answers_file(self) -> Path:
        """获取自定义答案文件路径"""
        return self._get_config_dir() / "custom_answers.json"
    
    def _load_answers(self) -> List[str]:
        """加载答案库"""
        answers = BASE_ANSWERS.copy()
        
        # 尝试从外部文件加载更多答案
        custom_answers_file = self._get_custom_answers_file()
        try:
            if custom_answers_file.exists():
                with open(custom_answers_file, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    custom_answers = custom_data.get("answers", [])
                    answers.extend(custom_answers)
                    logger.info(f"已加载 {len(custom_answers)} 个自定义答案")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"加载自定义答案失败: {e}")
        
        return answers
    
    def get_answer(self, question: str) -> str:
        """获取随机答案"""
        question = question.strip()
        if not question:
            return "请提出一个具体的问题。"
        
        answer = random.choice(self.answers)
        
        # 记录历史
        timestamp = datetime.now().isoformat()
        self.history.append({
            "timestamp": timestamp,
            "question": question,
            "answer": answer
        })
        
        # 更新统计
        self.stats["total_queries"] += 1
        self.stats["popular_questions"][question] = self.stats["popular_questions"].get(question, 0) + 1
        
        # 保持历史记录不超过100条
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        return answer
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取查询历史"""
        return self.history[-limit:] if limit > 0 else []
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()  # 返回副本以避免外部修改
    
    def add_custom_answer(self, answer: str) -> bool:
        """添加自定义答案"""
        if not answer or answer in self.answers:
            return False
            
        self.answers.append(answer)
        
        # 保存到文件
        try:
            custom_answers = [a for a in self.answers if a not in self._base_answers_set]
            data = {"answers": custom_answers}
            
            with open(self._get_custom_answers_file(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功添加自定义答案: {answer}")
            return True
        except IOError as e:
            logger.error(f"保存自定义答案失败: {e}")
            # 回滚添加的答案
            self.answers.remove(answer)
            return False

# 创建答案之书实例
answer_book = AnswerBook()

@mcp.tool()
def ask_question(question: str) -> str:
    """
    向答案之书提问并获得一个随机而富有哲理的答案
    
    Args:
        question: 你想要询问的问题，可以是任何方面的疑问
        
    Returns:
        一个随机的智慧答案
    """
    return answer_book.get_answer(question)

@mcp.tool()
def get_recent_history(limit: int = 5) -> List[dict]:
    """
    获取最近的提问历史记录
    
    Args:
        limit: 要获取的历史记录数量，默认为5条
        
    Returns:
        包含时间戳、问题和答案的历史记录列表
    """
    return answer_book.get_history(limit)

@mcp.tool()
def get_statistics() -> dict:
    """
    获取答案之书的使用统计信息
    
    Returns:
        包含总查询次数和热门问题的统计信息
    """
    return answer_book.get_stats()

@mcp.tool()
def add_custom_answer(answer_text: str) -> str:
    """
    添加自定义答案到答案库中
    
    Args:
        answer_text: 要添加的自定义答案文本
        
    Returns:
        添加成功或失败的消息
    """
    if answer_book.add_custom_answer(answer_text):
        return f"成功添加自定义答案: {answer_text}"
    else:
        return "添加自定义答案失败，可能是答案已存在或保存失败"

@mcp.tool()
def clear_history() -> str:
    """
    清空所有历史记录
    
    Returns:
        清空结果的消息
    """
    answer_book.history.clear()
    return "历史记录已清空"

@mcp.tool()
def get_answer_count() -> int:
    """
    获取当前答案库中的答案总数
    
    Returns:
        答案的总数量
    """
    return len(answer_book.answers)

def print_startup_info():
    """打印启动信息，但避免干扰MCP协议通信"""
    # 使用标准错误输出（stderr）而不是标准输出（stdout）
    import sys
    startup_message = (
        "=" * 60 + "\n"
        "        答案之书 MCP 服务         \n"
        "=" * 60 + "\n"
        "一个基于Model Context Protocol的智慧答案生成服务\n"
        "为你的问题提供随机而富有哲理的答案\n"
        "=" * 60 + "\n"
        f"✓ 已加载 {len(answer_book.answers)} 个答案\n"
        "✓ MCP服务已启动成功\n"
        "✓ 支持多种MCP客户端连接\n"
        "=" * 60 + "\n"
        "如何使用:\n"
        "1. 使用支持MCP协议的客户端软件连接\n"
        "2. 可用命令:\n"
        "   - ask_question(question='你的问题') - 获取答案\n"
        "   - get_recent_history(limit=5) - 查看历史记录\n"
        "   - get_statistics() - 获取使用统计\n"
        "   - add_custom_answer(answer_text='答案') - 添加自定义答案\n"
        "   - get_answer_count() - 查看答案总数\n"
        "   - clear_history() - 清空历史记录\n"
        "=" * 60 + "\n"
        "服务运行中，请不要关闭此窗口...\n"
    )
    sys.stderr.write(startup_message)
    sys.stderr.flush()

def main():
    """uvx入口函数"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        # 版本信息也输出到stderr，避免干扰MCP协议通信
        sys.stderr.write("答案之书 MCP 服务 v1.0.0\n")
        sys.stderr.flush()
        return
    
    # 打印详细的启动信息
    print_startup_info()
    
    # 启动服务
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()