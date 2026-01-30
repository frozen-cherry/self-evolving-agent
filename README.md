# Self-Evolving AI Assistant

一个可自我进化的 Telegram AI 助理，基于 Claude 构建。

## ✨ 核心特性

- 🔍 **联网搜索** - 实时获取新闻、价格、事件等信息
- 💻 **代码执行** - 运行 Python 代码进行计算、处理数据、调用 API
- 🔧 **自我进化** - 自动创建新工具来扩展自己的能力
- 🧠 **持久记忆** - 记住重要信息，跨对话保持上下文
- 🔄 **远程更新** - 通过 Telegram 命令自动 git pull 并重启

## 🚀 快速开始

### 1. 准备工作

你需要：

- Telegram Bot Token（从 [@BotFather](https://t.me/BotFather) 获取）
- MiniMax API Key（从 [MiniMax Platform](https://platform.minimax.io) 获取）
- Brave Search API Key（从 [Brave Search API](https://brave.com/search/api/) 获取，每月免费 2000 次）
- 一台 VPS（Ubuntu 22.04，2核4G 足够）

### 2. 部署

```bash
# 克隆项目
git clone https://github.com/frozen-cherry/self-evolving-agent.git
cd self-evolving-agent

# 复制配置模板
cp config.example.py config.py

# 编辑配置，填入你的 API Keys
nano config.py
```

配置文件说明：

```python
TELEGRAM_TOKEN = "你的Telegram Bot Token"
MINIMAX_API_KEY = "你的MiniMax API Key"
BRAVE_API_KEY = "你的Brave Search API Key"

# 可选配置
ALLOWED_USERS = []  # 限制允许使用的用户ID，空列表表示所有人
MINIMAX_MODEL = "MiniMax-M2"  # 可选: MiniMax-M2, MiniMax-M2.1, MiniMax-M2.1-lightning
```

### 3. 运行

**方式一：直接运行**

```bash
pip install -r requirements.txt
python bot.py
```

**方式二：Docker（推荐生产环境）**

```bash
docker compose up -d
docker compose logs -f  # 查看日志
```

## 📖 使用方法

### 命令列表

| 命令      | 功能                    |
| --------- | ----------------------- |
| `/start`  | 显示欢迎信息            |
| `/help`   | 显示帮助                |
| `/reset`  | 清除对话历史            |
| `/tools`  | 列出所有可用工具        |
| `/model`  | 切换模型（sonnet/opus） |
| `/update` | 远程更新并重启 Bot      |
| `/reload` | 重新加载自定义工具      |

### 示例对话

**🔍 实时信息查询**

```
你：BTC 现在什么价格？
Bot：[搜索] 当前 BTC 价格是 $96,500...
```

**💻 代码执行**

```
你：帮我算一下 10000 美元年化 15% 复利 5 年后是多少
Bot：[执行代码] 计算结果是 $20,113.57
```

**🔧 自动创建工具**

```
你：创建一个获取 Binance 价格的工具
Bot：✅ 工具「get_crypto_price」创建成功！

你：ETH 价格多少？
Bot：[调用 get_crypto_price] ETHUSDT: $3,456.78
```

**🧠 记忆功能**

```
你：记住我的 Solana 钱包地址是 xxx
Bot：✅ 已记住 [wallet] solana_main

你：我的 Solana 地址是什么？
Bot：你的 Solana 钱包地址是 xxx
```

## 🔧 内置工具

| 工具名           | 功能                     |
| ---------------- | ------------------------ |
| `web_search`     | 联网搜索（Brave Search） |
| `run_python`     | 执行 Python 代码         |
| `create_tool`    | 创建新工具               |
| `update_tool`    | 更新工具代码             |
| `delete_tool`    | 删除工具                 |
| `list_tools`     | 列出所有工具             |
| `view_tool_code` | 查看工具源码             |
| `remember`       | 记住重要信息             |
| `recall`         | 搜索记忆                 |
| `list_memories`  | 列出所有记忆             |
| `forget`         | 删除记忆                 |

## 📁 项目结构

```
self-evolving-agent/
├── bot.py              # Telegram Bot 入口
├── agent.py            # AI Agent 核心
├── tool_manager.py     # 工具管理器
├── memory_manager.py   # 记忆管理器
├── config.example.py   # 配置模板
├── requirements.txt    # Python 依赖
├── Dockerfile
├── docker-compose.yml
└── tools/
    ├── _builtin/       # 内置工具
    └── _custom/        # AI 创建的自定义工具
        ├── manifest.json
        └── *.py
```

## 🔒 安全说明

1. **代码执行沙盒**：Python 代码有超时限制（默认 30 秒），禁止危险操作
2. **用户白名单**：通过 `ALLOWED_USERS` 限制允许使用的用户
3. **配置保护**：`config.py` 已在 `.gitignore` 中，不会被提交

## ❓ 常见问题

**Q: Bot 没有响应？**

- 检查 Telegram Token 是否正确
- 检查服务器是否能访问 Telegram API（可能需要代理）
- 查看日志：`docker compose logs -f` 或 `~/self-evolving-agent/logs/bot.log`

**Q: 搜索功能不工作？**

- 确认已配置 `BRAVE_API_KEY`
- Brave Search 免费版每月 2000 次，每秒 1 次限制

**Q: 如何备份？**

- 备份 `config.py`（配置）
- 备份 `tools/_custom/`（自定义工具）
- 备份 `~/self-evolving-agent/workspace/memory/`（记忆数据）

## 📄 License

MIT

## ⚠️ 免责声明

本项目仅供学习和研究使用。使用者需自行承担使用本项目所产生的一切风险和责任，包括但不限于：

- AI 生成内容的准确性和可靠性
- 代码执行可能带来的系统风险
- API 调用产生的费用
- 因使用本项目导致的任何直接或间接损失

作者不对任何因使用本项目而产生的损失承担责任。
