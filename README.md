# Self-Evolving AI Assistant

一个可自我进化的 Telegram AI 助理。它可以：

- 联网搜索获取实时信息
- 执行 Python 代码
- **自动创建新工具来扩展自己的能力**

## 快速开始

### 1. 准备工作

你需要：

- Telegram Bot Token（从 @BotFather 获取）
- Claude API Key（从 console.anthropic.com 获取）
- 一台 VPS（2核4G 足够）

### 2. 配置

复制配置模板并填入你的 API Keys：

```bash
cp config.example.py config.py
```

然后编辑 `config.py`：

```python
TELEGRAM_TOKEN = "你的Telegram Bot Token"
CLAUDE_API_KEY = "你的Claude API Key"

# 可选：限制允许使用的用户
ALLOWED_USERS = []  # 空列表表示允许所有人
# ALLOWED_USERS = [123456789]  # 只允许指定用户
```

### 3. 运行

**方式一：Docker（推荐）**

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

**方式二：直接运行**

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python bot.py
```

## 使用方法

### 基本命令

- `/start` - 显示欢迎信息
- `/help` - 显示帮助
- `/reset` - 清除对话历史
- `/tools` - 列出所有可用工具
- `/reload` - 重新加载自定义工具

### 示例对话

**获取信息：**

```
你：BTC 现在多少钱？
Bot：[自动搜索或调用 API] BTC 当前价格是 $96,500...
```

**执行代码：**

```
你：帮我算一下 10000 美元年化 15% 复利 5 年是多少
Bot：[执行 Python 代码] 计算结果是 $20,113.57
```

**自我扩展：**

```
你：帮我创建一个获取 Binance BTC 价格的工具
Bot：好的，我来创建这个工具...
    ✅ 工具「get_btc_price」创建成功！

你：BTC 价格多少？
Bot：[调用 get_btc_price] 当前 BTC 价格是 $96,532.00
```

## 工具系统

### 内置工具

| 工具名         | 功能             |
| -------------- | ---------------- |
| web_search     | 联网搜索         |
| run_python     | 执行 Python 代码 |
| create_tool    | 创建新工具       |
| list_tools     | 列出所有工具     |
| view_tool_code | 查看工具代码     |
| update_tool    | 更新工具         |
| delete_tool    | 删除工具         |

### 自定义工具

AI 创建的工具会保存在 `tools/_custom/` 目录下：

- `manifest.json` - 工具清单
- `xxx.py` - 工具代码文件

这些文件会被持久化，重启后依然可用。

### 创建工具示例

让 AI 创建一个获取加密货币价格的工具：

```
你：创建一个工具，可以获取任意加密货币在 Binance 的价格

Bot：好的，我来创建这个工具...

[AI 自动创建 get_crypto_price 工具，包含以下代码]

import requests

def run(symbol: str = "BTCUSDT"):
    """获取加密货币价格"""
    try:
        resp = requests.get(
            f"https://api.binance.com/api/v3/ticker/price",
            params={"symbol": symbol.upper()},
            timeout=10
        )
        data = resp.json()
        return f"{symbol.upper()}: ${float(data['price']):,.2f}"
    except Exception as e:
        return f"获取失败: {str(e)}"
```

之后就可以直接使用：

```
你：ETH 价格多少？
Bot：[调用 get_crypto_price(symbol="ETHUSDT")] ETHUSDT: $3,456.78
```

## 目录结构

```
self-evolving-agent/
├── bot.py              # Telegram Bot 入口
├── agent.py            # AI Agent 核心
├── tool_manager.py     # 工具管理器
├── config.py           # 配置文件
├── requirements.txt    # Python 依赖
├── Dockerfile
├── docker-compose.yml
└── tools/
    ├── _builtin/       # 内置工具（代码在 tool_manager.py 中）
    └── _custom/        # AI 创建的自定义工具
        ├── manifest.json
        └── *.py
```

## 安全说明

1. **代码执行沙盒**：执行的代码有超时限制，且禁止危险操作（如 os.system）
2. **用户白名单**：可以通过 `ALLOWED_USERS` 限制允许使用的用户
3. **API Key 保护**：不要把 config.py 提交到公开仓库

## 常见问题

**Q: Bot 没有响应？**

- 检查 Telegram Token 是否正确
- 检查网络是否能访问 Telegram API
- 查看 Docker 日志：`docker compose logs -f`

**Q: 工具创建失败？**

- AI 生成的代码可能有错误，查看错误信息
- 可以让 AI 重新创建或手动修复代码

**Q: 如何备份工具？**

- 备份 `tools/_custom/` 目录即可

## License

MIT
