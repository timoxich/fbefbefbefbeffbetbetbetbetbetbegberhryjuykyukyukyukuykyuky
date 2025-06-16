from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import aiohttp
import asyncio
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7863135976:AAGlQmvWoPPqKtb9kn6WjgiL96AG0a8EFkw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

UID_COUNTER = {}
PAID_USERS = set()

async def main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️О Магазине", callback_data="about")
    kb.button(text="✨Моя Подписка", callback_data="subscription")
    kb.button(text="👤Профиль", callback_data="profile")
    return kb.as_markup()

async def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="back")
    return kb.as_markup()

@dp.message(CommandStart(deep_link=True))
async def activate_command(msg, command: CommandStart):
    code = command.args
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://elevenx.onrender.com/ZJEfYIMk_activate_key",
            params={"code": code}
        ) as resp:
            res = await resp.json()
    if res.get("success"):
        key = res["key"]
        user_id = msg.from_user.id
        PAID_USERS.add(user_id)
        await msg.answer(f"🔑 Ключ выдан: <code>{key}</code>", parse_mode=ParseMode.HTML)
    else:
        await msg.answer("❌ Ошибка активации.")

@dp.message(CommandStart())
async def start(msg):
    keyboard = await main_menu_keyboard()
    await msg.answer("👋 Добро пожаловать в бота eLevenX Shop!", reply_markup=keyboard)

@dp.callback_query(F.data == "about")
async def about(call):
    kb = await back_button()
    await call.message.edit_text(
        "✨ О магазине\n\n"
        "eLevenX – Уникальное DLC для Standoff 2\n"
        "В DLC присутствует огромное количество функций.\n"
        "С нашим DLC вы можете получить удовольствие от игры, не боясь получить игровую блокировку.\n"
        "Быстрые обновления на последние версии игры.\n"
        "Важно! Для использования DLC необходимы рут-права!\n\n"
        "💎 Наш Telegram канал: https://t.me/elevenx8",
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query(F.data == "profile")
async def profile(call):
    uid = UID_COUNTER.get(call.from_user.id)
    if uid is None:
        uid = len(UID_COUNTER) + 1
        UID_COUNTER[call.from_user.id] = uid
    status = "Платный подписчик" if call.from_user.id in PAID_USERS else "Без подписки"
    kb = await back_button()
    await call.message.edit_text(
        f"✨ Ваш профиль\n\n"
        f"Имя: {call.from_user.full_name}\n"
        f"Telegram ID: {call.from_user.id}\n"
        f"UID в боте: {uid}\n"
        f"Статус в боте: {status}",
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query(F.data == "subscription")
async def subscription(call):
    user_id = call.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://elevenx.onrender.com//moASnrwD_get_key_info",
            params={"key": f"UID_{user_id}"}
        ) as resp:
            data = await resp.json()
    kb = await back_button()
    if not data.get("found", False):
        if user_id in PAID_USERS:
            PAID_USERS.discard(user_id)
        await call.message.edit_text("❌ У вас нет активной подписки. Купить можно у @hexwound", reply_markup=kb)
    else:
        PAID_USERS.add(user_id)
        await call.message.edit_text(
            f"🔑 Ключ: {data['key']}\n"
            f"📱 Устройство: {data['hwid']}\n"
            f"🛡️ Статус DLC: {data['dlc_status']}\n\n"
            f"ℹ️ Получить DLC и все необходимые файлы можно у @hexwound",
            reply_markup=kb
        )
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call):
    keyboard = await main_menu_keyboard()
    await call.message.edit_text("👋 Добро пожаловать в бота eLevenX Shop!", reply_markup=keyboard)
    await call.answer()

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
