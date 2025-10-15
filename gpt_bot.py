import logging
import os
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем токены из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Настройка клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Настраиваем логирование
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []  # очищаем память при старте
    await update.message.reply_text("👋 Привет! Я ChatGPT-бот. Пиши что угодно — я запомню контекст разговора!")

# Основная функция ответа
async def chatgpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    user_id = update.message.from_user.id
    logger.info(f"Сообщение от {user_id}: {user_message}")

    # Инициализируем историю для пользователя, если её ещё нет
    if "history" not in context.user_data:
        context.user_data["history"] = []

    # Добавляем сообщение пользователя в историю
    context.user_data["history"].append({"role": "user", "content": user_message})

    try:
        # Отображаем, что бот “печатает”
        await update.message.chat.send_action(action=ChatAction.TYPING)

        # Запрашиваем ответ от ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты дружелюбный Telegram-бот-помощник. Пиши естественно и с эмоциями."},
                *context.user_data["history"],
            ],
            max_tokens=400,
        )

        bot_reply = response.choices[0].message.content.strip()
        logger.info(f"Ответ бота: {bot_reply}")

        # Добавляем ответ бота в историю
        context.user_data["history"].append({"role": "assistant", "content": bot_reply})

        # Имитация “живого” ответа (печатает по частям)
        await send_typing_reply(update, bot_reply)

    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Произошла ошибка при обращении к ChatGPT.")

# Функция имитации “живого” набора текста
async def send_typing_reply(update: Update, text: str, delay_per_chunk: float = 0.5):
    chunks = []
    words = text.split()

    # Разбиваем длинный ответ на части по ~30 слов
    chunk = []
    for word in words:
        chunk.append(word)
        if len(chunk) >= 30:
            chunks.append(" ".join(chunk))
            chunk = []
    if chunk:
        chunks.append(" ".join(chunk))

    # Отправляем части с имитацией “набора”
    for i, part in enumerate(chunks):
        if i == 0:
            await update.message.reply_text(part)
        else:
            await update.message.chat.send_action(ChatAction.TYPING)
            await asyncio.sleep(delay_per_chunk)
            await update.message.reply_text(part)

# Основная функция запуска бота
def main():
    logger.info("🚀 Запуск Telegram-бота...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chatgpt_handler))

    logger.info("✅ Бот готов к приёму сообщений.")
    app.run_polling()

if __name__ == "__main__":
    main()

