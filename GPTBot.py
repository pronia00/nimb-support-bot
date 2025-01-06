import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv  # Подключаем dotenv
import os
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import APIKeyAuth

# Загрузка токена из .env
load_dotenv()  # Загрузка переменных из файла .env
print("Загруженные переменные окружения:")
print(f"FOLDER_ID: {os.getenv('FOLDER_ID')}")
print(f"TELEGRAM_TOKEN: {'Найден' if os.getenv('TELEGRAM_TOKEN') else 'Не найден'}")
print(f"APIKeyAuth: {'Найден' if os.getenv('APIKeyAuth') else 'Не найден'}")

bot_token = os.getenv("TELEGRAM_TOKEN")
ygpt_api_key = os.getenv("APIKeyAuth")
folder_id = os.getenv("FOLDER_ID")

if not folder_id:
    raise ValueError("FOLDER_ID не найден. Убедитесь, что он указан в файле .env.")

if not bot_token:
    raise ValueError("TELEGRAM_TOKEN не найден. Убедитесь, что он указан в файле .env.")

if not ygpt_api_key:
    raise ValueError("YandexGPT-APIKeyAuth не найден. Убедитесь, что он указан в файле .env.")

# Инициализация Yandex Cloud ML SDK
sdk = YCloudML(
    folder_id=folder_id,
    auth=APIKeyAuth(ygpt_api_key)
)

# Настройка модели YandexGPT
model = sdk.models.completions("yandexgpt")
model = model.configure(temperature=0.5)



# Инициализация бота
bot = Bot(
    token=bot_token,
    session=AiohttpSession(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
start_message = "Привет!\nЧтобы начать пользоваться ботом поддержки Nimb, напиши о чем ты хочешь узнать."


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer(start_message)

@dp.message()
async def handle_message(message: types.Message):
    try:
        # Получаем текст сообщения от пользователя
        user_text = message.text
        
        # Отправляем запрос к YandexGPT
        result = model.run(user_text)
        
        # Получаем ответ от модели
        bot_response = result.alternatives[0].text
        
        # Отправляем ответ пользователю
        await message.answer(bot_response)
        
    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await message.answer("Извините, произошла ошибка при обработке вашего запроса.")


async def main():
    # Создаем бота и диспетчера
    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # Регистрируем обработчики
    dp.message.register(send_welcome, CommandStart())
    dp.message.register(handle_message)  # Регистрируем обработчик всех сообщений

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: %(levelname)s: %(message)s"
    )
    
    # Запускаем поллинг
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())