import logging
import os
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем токены из .env (или Render env)
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Проверяем на случай скрытых символов
print("TELEGRAM_TOKEN:", repr(TELEGRAM_TOKEN))

# Настраиваем OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я ChatGPT-бот. Напиши мне сообщение — и я отвечу!")

# Обработка сообщений
async def chatgpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    logger.info(f"Сообщение от {user_id}: {user_message}")

    try:
        await update.message.chat.send_action(action=ChatAction.TYPING)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты дружелюбный Telegram-бот-помощник."},
                {"role": "user", "content": user_message},
            ],
        )

        bot_reply = response.choices[0].message.content.strip()
        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Ошибка при работе с OpenAI: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Произошла ошибка при обращении к ChatGPT.")

# Основной запуск бота
def main():
    logger.info("🚀 Запуск Telegram-бота...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chatgpt_handler))

    logger.info("✅ Бот готов к приёму сообщений.")
    app.run_polling()

if __name__ == "__main__":
    main()
