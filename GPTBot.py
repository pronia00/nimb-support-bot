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
bot_token = os.getenv("TELEGRAM_TOKEN")
ygpt_api_key = os.getenv("APIKeyAuth")

if not bot_token:
    raise ValueError("TELEGRAM_TOKEN не найден. Убедитесь, что он указан в файле .env.")

if not ygpt_api_key:
    raise ValueError("YandexGPT-APIKeyAuth не найден. Убедитесь, что он указан в файле .env.")

# Инициализация Yandex Cloud ML SDK
sdk = YCloudML(
    folder_id="aje1cg8edv69esmdebn9",  # Замените на ваш folder_id
    auth=APIKeyAuth(ygpt_api_key)
)

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


async def main():
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(levelname)s: %(message)s"
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())