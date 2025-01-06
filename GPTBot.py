import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv  # Подключаем dotenv
import os

# Загрузка токена из .env
load_dotenv()  # Загрузка переменных из файла .env
bot_token = os.getenv("TELEGRAM_TOKEN")

if not bot_token:
    raise ValueError("TELEGRAM_TOKEN не найден. Убедитесь, что он указан в файле .env.")


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