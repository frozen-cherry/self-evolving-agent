"""
Telegram Bot - 主入口
"""

import asyncio
import logging
import base64
import tempfile
import os
from io import BytesIO
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from telegram.constants import ChatAction

from agent import chat, get_current_model, set_model, AVAILABLE_MODELS
from tool_manager import tool_manager
from config import TELEGRAM_TOKEN, ALLOWED_USERS, MAX_HISTORY_ROUNDS


async def download_image_as_base64(photo, context) -> tuple[str, str]:
    """下载图片并转为 base64"""
    file = await context.bot.get_file(photo.file_id)
    
    # 下载到内存
    bio = BytesIO()
    await file.download_to_memory(bio)
    bio.seek(0)
    
    # 转 base64
    image_data = base64.standard_b64encode(bio.read()).decode("utf-8")
    
    # 判断格式（Telegram 图片一般是 jpeg）
    media_type = "image/jpeg"
    
    return image_data, media_type


async def transcribe_voice(voice, context) -> str:
    """语音转文字（使用 OpenAI Whisper API）"""
    import httpx
    from config import OPENAI_API_KEY
    
    if not OPENAI_API_KEY:
        return None
    
    # 下载语音文件
    file = await context.bot.get_file(voice.file_id)
    bio = BytesIO()
    await file.download_to_memory(bio)
    bio.seek(0)
    
    # Telegram 语音是 ogg 格式
    # 调用 OpenAI Whisper API
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": ("voice.ogg", bio, "audio/ogg")},
            data={"model": "whisper-1"}
        )
        
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            logger.error(f"Whisper API 错误: {response.text}")
            return None

# 配置日志（同时输出到文件和终端）
import os
LOG_DIR = os.path.expanduser("~/self-evolving-agent/logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 禁用冗余的第三方库日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 存储用户对话历史
user_histories = {}


def check_user_allowed(user_id: int) -> bool:
    """检查用户是否有权限使用 Bot"""
    if not ALLOWED_USERS:  # 空列表表示允许所有人
        return True
    return user_id in ALLOWED_USERS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    user_id = update.effective_user.id
    
    if not check_user_allowed(user_id):
        await update.message.reply_text("⛔ 你没有权限使用此 Bot")
        return
    
    welcome_text = """🤖 **Self-Evolving AI Assistant**

我是一个可自我进化的 AI 助理，具备以下能力：

📡 **联网搜索** - 获取实时信息
💻 **代码执行** - 运行 Python 代码
🔧 **自我扩展** - 创建新工具来扩展能力

**命令：**
/reset - 重置对话历史
/tools - 查看当前所有工具
/model - 切换模型 (sonnet/opus)
/help - 显示帮助信息

直接发消息给我就可以开始对话！"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    if not check_user_allowed(update.effective_user.id):
        return
    
    help_text = """📖 **使用帮助**

**基本用法：**
直接发送消息即可对话，AI 会根据需要自动使用工具。

**示例：**
• "BTC 现在多少钱？" - 会自动搜索或调用 API
• "帮我写个脚本计算复利" - 会编写并执行代码
• "创建一个获取 ETH 价格的工具" - 会创建新工具

**命令：**
• /start - 显示欢迎信息
• /reset - 清除对话历史
• /tools - 列出所有可用工具
• /model - 切换模型 (sonnet/opus)
• /reload - 重新加载自定义工具
• /help - 显示此帮助

**自我进化：**
当 AI 发现缺少某个能力时，它可以自己创建新工具。
这些工具会被保存下来，以后可以直接使用。"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /reset 命令"""
    user_id = update.effective_user.id
    
    if not check_user_allowed(user_id):
        return
    
    user_histories.pop(user_id, None)
    await update.message.reply_text("✅ 对话历史已清除")


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /tools 命令"""
    if not check_user_allowed(update.effective_user.id):
        return
    
    tools_list = tool_manager._list_tools()
    await update.message.reply_text(tools_list, parse_mode='Markdown')


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /reload 命令"""
    if not check_user_allowed(update.effective_user.id):
        return
    
    result = tool_manager.reload_tools()
    await update.message.reply_text(result)


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /model 命令 - 切换或查看当前模型"""
    if not check_user_allowed(update.effective_user.id):
        return
    
    args = context.args
    
    if not args:
        # 显示当前模型和可用选项
        current = get_current_model()
        available = ", ".join(AVAILABLE_MODELS.keys())
        await update.message.reply_text(
            f"🤖 **当前模型:** `{current}`\n\n"
            f"**可用模型:** {available}\n\n"
            f"**切换方法:** `/model sonnet` 或 `/model opus`",
            parse_mode='Markdown'
        )
    else:
        # 切换模型
        result = set_model(args[0])
        await update.message.reply_text(result)


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /update 命令 - git pull 并重启 Bot"""
    if not check_user_allowed(update.effective_user.id):
        return
    
    import subprocess
    import sys
    
    await update.message.reply_text("🔄 正在检查更新...")
    
    try:
        # 执行 git pull
        result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=30
        )
        
        output = result.stdout.strip()
        
        if "Already up to date" in output or "Already up-to-date" in output:
            await update.message.reply_text("✅ 已是最新版本，无需更新")
            return
        
        # 有更新，发送更新信息并重启
        await update.message.reply_text(
            f"📥 更新完成！\n```\n{output[:500]}\n```\n\n🔄 正在重启...",
            parse_mode='Markdown'
        )
        
        # 等待消息发送
        await asyncio.sleep(1)
        
        # 原地重启进程
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ git pull 超时")
    except Exception as e:
        await update.message.reply_text(f"❌ 更新失败: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通文本消息"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if not check_user_allowed(user_id):
        await update.message.reply_text("⛔ 你没有权限使用此 Bot")
        return
    
    # 显示正在输入
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    # 发送处理中提示
    thinking_message = await update.message.reply_text("🤔 思考中...")
    
    # 获取当前事件循环（用于线程安全调度）
    loop = asyncio.get_event_loop()
    
    def on_tool_start(name, params):
        """工具开始执行时的回调（从线程中调用）"""
        # 生成简短的参数摘要
        if name == "run_python":
            code = str(params.get("code", ""))[:50].replace('\n', ' ')
            param_summary = code + "..."
        elif name == "web_search":
            param_summary = params.get('query', '')
        else:
            param_summary = str(params)[:50]
        
        status_text = f"🔧 {name}: {param_summary}"
        
        # 使用线程安全的方式调度异步任务
        async def update_message():
            try:
                await thinking_message.edit_text(status_text)
            except:
                pass
        
        loop.call_soon_threadsafe(lambda: asyncio.create_task(update_message()))
    
    try:
        # 获取历史
        history = user_histories.get(user_id, [])
        
        # 调用 Agent（在线程池中执行，传入工具状态回调）
        logger.info(f"用户 {user_id}: {user_message[:50]}...")
        response, new_history = await loop.run_in_executor(
            None, 
            lambda: chat(user_message, history, on_tool_start=on_tool_start)
        )
        
        # 更新历史（保留最近 N 轮）
        max_messages = MAX_HISTORY_ROUNDS * 2  # 每轮包含 user 和 assistant
        user_histories[user_id] = new_history[-max_messages:]
        
        # 删除"思考中"消息
        await thinking_message.delete()
        
        # 发送回复（处理长消息）
        await send_long_message(update, response)
        
        logger.info(f"回复用户 {user_id}: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"处理消息出错: {e}", exc_info=True)
        await thinking_message.edit_text(f"❌ 出错了: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理图片消息"""
    user_id = update.effective_user.id
    
    if not check_user_allowed(user_id):
        await update.message.reply_text("⛔ 你没有权限使用此 Bot")
        return
    
    # 显示正在输入
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    # 发送处理中提示
    thinking_message = await update.message.reply_text("🖼️ 处理图片中...")
    
    try:
        # 获取最大尺寸的图片
        photo = update.message.photo[-1]
        
        # 下载并转 base64
        image_data, media_type = await download_image_as_base64(photo, context)
        
        # 获取图片说明文字（如果有）
        caption = update.message.caption or "请看这张图片"
        
        # 构建带图片的消息内容
        user_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data
                }
            },
            {
                "type": "text",
                "text": caption
            }
        ]
        
        # 获取历史
        history = user_histories.get(user_id, [])
        
        # 调用 Agent（传入图片内容）
        logger.info(f"用户 {user_id} 发送图片: {caption[:30]}...")
        response, new_history = chat(user_content, history)
        
        # 更新历史
        max_messages = MAX_HISTORY_ROUNDS * 2
        user_histories[user_id] = new_history[-max_messages:]
        
        # 删除"处理中"消息
        await thinking_message.delete()
        
        # 发送回复
        await send_long_message(update, response)
        
        logger.info(f"回复用户 {user_id}: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"处理图片出错: {e}", exc_info=True)
        await thinking_message.edit_text(f"❌ 处理图片出错: {str(e)}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理语音消息"""
    user_id = update.effective_user.id
    
    if not check_user_allowed(user_id):
        await update.message.reply_text("⛔ 你没有权限使用此 Bot")
        return
    
    # 检查是否配置了 OpenAI API Key
    from config import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        await update.message.reply_text("⚠️ 语音功能需要配置 OPENAI_API_KEY")
        return
    
    # 显示正在处理
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    thinking_message = await update.message.reply_text("🎤 识别语音中...")
    
    try:
        # 获取语音
        voice = update.message.voice
        
        # 转文字
        text = await transcribe_voice(voice, context)
        
        if not text:
            await thinking_message.edit_text("❌ 语音识别失败")
            return
        
        # 更新提示
        await thinking_message.edit_text(f"🎤 识别结果：{text}\n\n🤔 思考中...")
        
        # 获取历史
        history = user_histories.get(user_id, [])
        
        # 调用 Agent
        logger.info(f"用户 {user_id} 语音: {text[:50]}...")
        response, new_history = chat(text, history)
        
        # 更新历史
        max_messages = MAX_HISTORY_ROUNDS * 2
        user_histories[user_id] = new_history[-max_messages:]
        
        # 删除"处理中"消息
        await thinking_message.delete()
        
        # 发送回复（带上识别结果）
        full_response = f"🎤 _{text}_\n\n{response}"
        await send_long_message(update, full_response)
        
        logger.info(f"回复用户 {user_id}: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"处理语音出错: {e}", exc_info=True)
        await thinking_message.edit_text(f"❌ 处理语音出错: {str(e)}")


async def send_long_message(update: Update, text: str, max_length: int = 4000):
    """发送长消息（自动分段）"""
    if len(text) <= max_length:
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    # 分段发送
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += ('\n' if current_chunk else '') + line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode='Markdown')
        except Exception:
            # Markdown 解析失败时用纯文本
            await update.message.reply_text(chunk)
        await asyncio.sleep(0.3)  # 避免发送过快


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """全局错误处理"""
    logger.error(f"发生错误: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ 发生了一个错误，请稍后重试"
        )


def main():
    """主函数"""
    print("🚀 启动 Self-Evolving AI Bot...")
    
    # 创建 Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("model", model_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("reload", reload_command))
    
    # 添加消息处理器
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # 添加图片处理器
    application.add_handler(MessageHandler(
        filters.PHOTO,
        handle_photo
    ))
    
    # 添加语音处理器
    application.add_handler(MessageHandler(
        filters.VOICE,
        handle_voice
    ))
    
    # 添加错误处理器
    application.add_error_handler(error_handler)
    
    # 启动 Bot
    print("✅ Bot 已启动，等待消息...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
