"""
配置文件 - 在这里填入你的 API Keys
"""

# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Claude API Key (从 Anthropic Console 获取)
CLAUDE_API_KEY = "YOUR_CLAUDE_API_KEY"

# Claude 模型选择
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# OpenAI API Key (用于语音识别，可选)
# 如果不需要语音功能，留空即可
OPENAI_API_KEY = ""

# Brave Search API Key (用于联网搜索)
# 从 https://brave.com/search/api/ 获取，每月免费 2000 次
BRAVE_API_KEY = ""

# 可选：允许使用 Bot 的 Telegram 用户 ID 列表
# 留空则允许所有人使用
# 获取你的 ID：给 @userinfobot 发消息
ALLOWED_USERS = []  # 例如: [123456789, 987654321]

# 代码执行超时时间（秒）
CODE_TIMEOUT = 30

# 对话历史保留轮数
MAX_HISTORY_ROUNDS = 10
