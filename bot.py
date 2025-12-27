import logging
import random
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import TOKEN, VERIFY_TIMEOUT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_state = {}  # {user_id: {"verified": bool, "answer": int, "expire": float}}

def send_verification(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    a = random.randint(2, 9)
    b = random.randint(2, 9)
    answer = a + b

    user_state[user_id] = {
        "verified": False,
        "answer": answer,
        "expire": time.time() + VERIFY_TIMEOUT,
    }

    update.message.reply_text(
        f"为了防止广告骚扰，请先完成验证：\n\n"
        f"请在 {VERIFY_TIMEOUT} 秒内回答：\n"
        f"{a} + {b} = ？\n\n"
        f"直接回复答案即可。"
    )

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id in user_state and user_state[user_id].get("verified"):
        update.message.reply_text("你已经通过验证，可以正常使用机器人。")
        return

    send_verification(update, context)

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id not in user_state:
        update.message.reply_text("请先发送 /start 开始验证。")
        return

    state = user_state[user_id]

    if state.get("verified"):
        update.message.reply_text(f"你已验证成功，我收到你的消息：{text}")
        return

    if time.time() > state.get("expire", 0):
        update.message.reply_text("验证已超时，请重新发送 /start。")
        del user_state[user_id]
        return

    if "http://" in text.lower() or "https://" in text.lower() or "t.me/" in text.lower():
        update.message.reply_text("检测到可疑链接，请先完成验证码验证。")
        return

    try:
        user_answer = int(text)
    except ValueError:
        update.message.reply_text("请直接回复数字答案。")
        return

    if user_answer == state.get("answer"):
        state["verified"] = True
        update.message.reply_text("验证通过！你现在可以正常使用机器人了。")
    else:
        update.message.reply_text("答案错误，请重新发送 /start。")
        del user_state[user_id]

def main():
    if not TOKEN:
        logger.error("TOKEN 为空，请检查环境变量 BOT_TOKEN 是否设置正确。")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    logger.info("Bot started polling")
    updater.idle()

if __name__ == "__main__":
    main()
