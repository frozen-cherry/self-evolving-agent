"""
Agent 核心模块 - 负责与 MiniMax API 交互和工具调用循环
"""

import anthropic
from tool_manager import tool_manager
from memory_manager import memory_manager
from config import MINIMAX_API_KEY, MINIMAX_MODEL

# 初始化 MiniMax 客户端（使用 Anthropic 兼容接口）
client = anthropic.Anthropic(
    api_key=MINIMAX_API_KEY,
    base_url="https://api.minimaxi.com/anthropic"
)

# 可用模型列表
AVAILABLE_MODELS = {
    "m2": "MiniMax-M2",
    "m2.1": "MiniMax-M2.1",
    "lightning": "MiniMax-M2.1-lightning",
}

# 当前使用的模型（默认从配置读取）
_current_model = MINIMAX_MODEL

def get_current_model() -> str:
    """获取当前模型"""
    return _current_model

def set_model(model_name: str) -> str:
    """切换模型，返回结果消息"""
    global _current_model
    
    model_name = model_name.lower()
    
    if model_name in AVAILABLE_MODELS:
        _current_model = AVAILABLE_MODELS[model_name]
        return f"✅ 已切换到 {model_name.upper()} ({_current_model})"
    elif model_name in AVAILABLE_MODELS.values():
        _current_model = model_name
        return f"✅ 已切换到 {_current_model}"
    else:
        available = ", ".join(AVAILABLE_MODELS.keys())
        return f"❌ 未知模型。可用模型: {available}"

# 系统提示词（基础部分）
SYSTEM_PROMPT_BASE = """你是一个强大的、可自我进化的 AI 助理。

## 你的核心能力

1. **联网搜索** - 获取实时信息、新闻、价格等
2. **执行代码** - 运行 Python 代码进行计算、调用 API、处理数据
3. **自我扩展** - 当发现缺少某个能力时，可以创建新工具来扩展自己
4. **后台任务** - 可以启动、管理、停止后台运行的监控脚本
5. **记忆系统** - 可以记住重要信息，下次对话时自动回忆
6. **定时任务** - 可以创建定时任务，在指定时间自动唤醒执行

## 关于记忆

你有持久化记忆能力。主动使用 `remember` 记住以下类型的信息：
- **wallet**: 创建的钱包地址、私钥存放位置
- **api**: API Key 位置、调用方法
- **secret**: 密码、密钥存放位置
- **knowledge**: 学到的知识（比如某 API 要收费了、某个方法不可行）
- **preference**: 用户的偏好和习惯

不用记的：一次性查询结果、临时计算过程、通用知识

使用 `recall` 可以搜索记忆，`list_memories` 可以列出所有记忆。

## 关于创建新工具

当用户需要一个你目前没有的功能时，你可以使用 `create_tool` 来创建新工具。

**创建工具的原则：**
- 只创建可复用的工具，不要为一次性任务创建
- 代码要健壮，处理好异常
- 必须包含 `def run(...)` 函数作为入口
- 参数要和 parameters 定义匹配
- 返回清晰的字符串结果

**⚠️ 修改工具的规则：**
- 修改或更新已有工具代码前，**必须先告知用户改动内容**
- 等待用户**明确允许**后才能执行 `update_tool` 操作
- 未经确认，禁止自动修改工具代码

## 关于后台任务

你可以使用 subprocess 启动后台进程。工作目录是 `~/self-evolving-agent/workspace/`

**启动后台监控任务示例：**
```python
import subprocess
import os

# 确保目录存在
os.makedirs(os.path.expanduser('~/self-evolving-agent/workspace/logs'), exist_ok=True)

# 启动后台任务
proc = subprocess.Popen(
    ['nohup', 'python3', os.path.expanduser('~/self-evolving-agent/workspace/monitor.py')],
    stdout=open(os.path.expanduser('~/self-evolving-agent/workspace/logs/monitor.log'), 'w'),
    stderr=subprocess.STDOUT,
    start_new_session=True
)
print(f"任务已启动，PID: {proc.pid}")
```

**查看运行中的任务：**
```python
import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
for line in result.stdout.split('\\n'):
    if 'workspace' in line and 'python' in line:
        print(line)
```

**停止任务：**
```python
import os
os.kill(PID, 9)  # PID 是进程号
```

## 工具管理

- `list_tools` - 查看当前所有工具
- `view_tool_code` - 查看某个工具的代码
- `update_tool` - 更新工具的代码或描述
- `delete_tool` - 删除不需要的工具

## 注意事项

- 先尝试用现有工具完成任务
- 如果现有工具不够，考虑是否值得创建新工具
- 代码执行有超时限制，复杂操作要注意
- 遇到错误时，分析原因并尝试修复
- 后台任务要记录好 PID，方便后续管理
- 重要信息要用 remember 记住

## 回复风格

- 简洁直接，不要过多废话
- 任务完成后给出清晰的结果
- 遇到问题时说明原因和解决方案
"""


def get_system_prompt() -> str:
    """获取完整的 system prompt，包含核心记忆"""
    core_memories = memory_manager.get_core_memories()
    
    if core_memories:
        return SYSTEM_PROMPT_BASE + f"\n\n## 你的记忆\n\n{core_memories}"
    else:
        return SYSTEM_PROMPT_BASE


def chat(user_message, history: list = None, max_iterations: int = 20, on_tool_start=None) -> tuple[str, list]:
    """
    与 Claude 对话，自动处理工具调用
    
    Args:
        user_message: 用户消息（字符串或包含图片的 list）
        history: 对话历史
        max_iterations: 最大工具调用循环次数
        on_tool_start: 可选回调函数，工具开始执行时调用，参数为 (tool_name, tool_input)
    
    Returns:
        (回复文本, 更新后的历史)
    """
    if history is None:
        history = []
    
    # 构建消息（支持纯文本或图片内容）
    if isinstance(user_message, str):
        message_content = user_message
    else:
        # 图片或复杂内容，直接使用
        message_content = user_message
    
    messages = history + [{"role": "user", "content": message_content}]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            # 调用 Claude API（每次获取最新的 system prompt，包含记忆）
            response = client.messages.create(
                model=_current_model,
                max_tokens=8192,
                system=get_system_prompt(),
                tools=tool_manager.get_schemas(),
                messages=messages
            )
        except anthropic.APIError as e:
            return f"❌ API 调用失败: {str(e)}", history
        
        # 检查是否需要调用工具
        if response.stop_reason == "tool_use":
            # 提取工具调用
            tool_calls = [block for block in response.content if block.type == "tool_use"]
            
            # 记录 assistant 的响应
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            # 执行每个工具并收集结果
            tool_results = []
            for tool_call in tool_calls:
                print(f"🔧 执行工具: {tool_call.name}")
                print(f"   参数: {tool_call.input}")
                
                # 通知外部（如 Telegram）
                if on_tool_start:
                    try:
                        on_tool_start(tool_call.name, tool_call.input)
                    except:
                        pass  # 通知失败不影响执行
                
                result = tool_manager.execute(tool_call.name, tool_call.input)
                
                # 截断过长的结果
                if len(result) > 10000:
                    result = result[:10000] + "\n\n... [结果过长，已截断]"
                
                print(f"   结果: {result[:200]}...")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
            
            # 添加工具结果
            messages.append({
                "role": "user",
                "content": tool_results
            })
        
        else:
            # 没有工具调用，提取最终文本
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            
            # 更新历史
            # 注意：如果是图片消息，历史中只保留文字描述（避免历史太大）
            if isinstance(user_message, list):
                # 提取文字部分
                text_parts = [item["text"] for item in user_message if item.get("type") == "text"]
                history_user_content = "[图片] " + " ".join(text_parts) if text_parts else "[图片]"
            else:
                history_user_content = user_message
            
            new_history = history + [
                {"role": "user", "content": history_user_content},
                {"role": "assistant", "content": final_text}
            ]
            
            return final_text, new_history
    
    # 超过最大迭代次数，让 AI 总结问题
    try:
        summary_response = client.messages.create(
            model=_current_model,
            max_tokens=1024,
            system="用中文简洁总结",
            messages=[{
                "role": "user", 
                "content": f"""刚才的任务执行了 {max_iterations} 次工具调用仍未完成。

请总结：
1. 任务目标是什么
2. 尝试了哪些方法
3. 卡在哪一步
4. 可能的解决方向

对话记录：
{str(messages[-6:]) if len(messages) > 6 else str(messages)}
"""
            }]
        )
        summary = ""
        for block in summary_response.content:
            if hasattr(block, "text"):
                summary += block.text
        
        return f"⚠️ 任务过于复杂，已达到最大执行次数。\n\n**问题总结：**\n{summary}", history
    except:
        return "⚠️ 任务过于复杂，已达到最大执行次数。请尝试分解任务。", history


def chat_stream(user_message: str, history: list = None, max_iterations: int = 10):
    """
    流式对话（用于未来扩展）
    目前简单包装 chat 函数
    """
    return chat(user_message, history, max_iterations)
