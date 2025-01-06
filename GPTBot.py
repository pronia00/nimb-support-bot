import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
import os
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import APIKeyAuth

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
bot_token = os.getenv("TELEGRAM_TOKEN")
ygpt_api_key = os.getenv("APIKeyAuth")
folder_id = os.getenv("FOLDER_ID")

# Проверка наличия необходимых переменных
for var_name, var_value in [
    ("FOLDER_ID", folder_id),
    ("TELEGRAM_TOKEN", bot_token),
    ("APIKeyAuth", ygpt_api_key)
]:
    if not var_value:
        raise ValueError(f"{var_name} не найден. Убедитесь, что он указан в файле .env.")

# Инициализация YandexGPT
sdk = YCloudML(
    folder_id=folder_id,
    auth=APIKeyAuth(ygpt_api_key)
)

# Настройка модели
model = sdk.models.completions("yandexgpt")
model = model.configure(temperature=0.5)

# Инициализация бота
bot = Bot(token=bot_token, session=AiohttpSession(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранилище контекста диалогов
dialog_contexts = {}

class MessageFormatter:
    @staticmethod
    def format_gpt_response(result):
        response_parts = []
        response_parts.append("<b>🤖 Ответ модели:</b>")
        response_parts.append(f"{result.alternatives[0].text}\n")
        
        response_parts.append("<b>📊 Статистика:</b>")
        response_parts.append(f"• Токенов во входном тексте: {result.usage.input_text_tokens}")
        response_parts.append(f"• Токенов в ответе: {result.usage.completion_tokens}")
        response_parts.append(f"• Всего токенов: {result.usage.total_tokens}")
        response_parts.append(f"• Статус: {result.alternatives[0].status}")
        response_parts.append(f"• Роль: {result.alternatives[0].role}")
        response_parts.append(f"• Версия модели: {result.model_version}")
        
        return "\n".join(response_parts)

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    welcome_text = """
<b>👋 Привет! Я бот на базе YandexGPT.</b>

<b>Доступные команды:</b>
• /help - показать это сообщение
• /new - начать новый диалог
• /system - установить системный промпт
• /temp - установить temperature (0.0-1.0)

Просто напишите сообщение, чтобы начать диалог!
"""
    await message.answer(welcome_text)

@dp.message(Command("new"))
async def new_dialog(message: types.Message):
    user_id = message.from_user.id
    dialog_contexts[user_id] = []
    await message.answer("🔄 Начат новый диалог!")

@dp.message(Command("system"))
async def set_system_prompt(message: types.Message):
    user_id = message.from_user.id
    system_prompt = message.text.replace("/system", "").strip()
    
    if not system_prompt:
        await message.answer("❌ Укажите системный промпт после команды!")
        return
        
    if user_id not in dialog_contexts:
        dialog_contexts[user_id] = []
        
    dialog_contexts[user_id] = [{"role": "system", "text": system_prompt}] + [
        msg for msg in dialog_contexts[user_id] if msg["role"] != "system"
    ]
    
    await message.answer(f"✅ Установлен системный промпт:\n<i>{system_prompt}</i>")

@dp.message(Command("temp"))
async def set_temperature(message: types.Message):
    try:
        temp = float(message.text.replace("/temp", "").strip())
        if 0 <= temp <= 1:
            global model
            model = model.configure(temperature=temp)
            await message.answer(f"✅ Temperature установлена на: {temp}")
        else:
            await message.answer("❌ Temperature должна быть от 0 до 1!")
    except ValueError:
        await message.answer("❌ Укажите числовое значение temperature!")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = """
<b>👋 Помощь по использованию бота</b>

<b>Доступные команды:</b>
• /help - показать это сообщение
• /new - начать новый диалог
• /system - установить системный промпт
• /temp - установить temperature (0.0-1.0)

<b>Примеры использования:</b>
• Просто напишите сообщение для диалога
• /system Ты - опытный программист
• /temp 0.7
"""
    await message.answer(help_text)

@dp.message()
async def handle_message(message: types.Message):
    try:
        user_id = message.from_user.id
        user_text = message.text
        
        # Инициализация контекста диалога если его нет
        if user_id not in dialog_contexts:
            dialog_contexts[user_id] = []
            
        # Добавление сообщения пользователя в контекст
        dialog_contexts[user_id].append({"role": "user", "text": user_text})
        
        # Получение ответа от модели
        result = model.run(dialog_contexts[user_id])
        
        # Добавление ответа в контекст
        dialog_contexts[user_id].append({
            "role": result.alternatives[0].role,
            "text": result.alternatives[0].text
        })
        
        # Форматирование и отправка ответа
        formatted_response = MessageFormatter.format_gpt_response(result)
        await message.answer(formatted_response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обработке запроса.")

async def main():
    # Регистрируем все обработчики
    dp.message.register(send_welcome, CommandStart())
    dp.message.register(send_help, Command("help"))
    dp.message.register(new_dialog, Command("new"))
    dp.message.register(set_system_prompt, Command("system"))
    dp.message.register(set_temperature, Command("temp"))
    dp.message.register(handle_message)  # Обработчик обычных сообщений должен быть последним

    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())