from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import aiohttp
import asyncio
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7863135976:AAGlQmvWoPPqKtb9kn6WjgiL96AG0a8EFkw"
ADMIN_IDS = {7899575088, 5361974069}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
UID_COUNTER = {}
PAID_USERS = set()
API_BASE = os.getenv("API_BASE") or "https://elevenx.onrender.com"  

async def main_menu_keyboard(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️О Магазине", callback_data="about")
    kb.button(text="✨Моя Подписка", callback_data="subscription")
    kb.button(text="👤Профиль", callback_data="profile")
    if is_admin:
        kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    return kb.as_markup()

async def back_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="back")
    return kb.as_markup()

@dp.message(CommandStart(deep_link=True))
async def activate_command(msg, command: CommandStart):
    code = command.args
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/activate_key", params={"code": code}) as resp:
            res = await resp.json()
    if res.get("success"):
        key = res["key"]
        PAID_USERS.add(msg.from_user.id)
        await msg.answer(f"🔑 Ключ выдан: <code>{key}</code>", parse_mode=ParseMode.HTML)
    else:
        await msg.answer("❌ Ошибка активации.")

@dp.message(CommandStart())
async def start(msg):
    is_admin = msg.from_user.id in ADMIN_IDS
    kb = await main_menu_keyboard(is_admin)
    await msg.answer("👋 Добро пожаловать!", reply_markup=kb)

@dp.callback_query(F.data == "about")
async def about(call):
    kb = await back_button()
    await call.message.edit_text("ℹ️ О магазине...", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == "profile")
async def profile(call):
    uid = UID_COUNTER.setdefault(call.from_user.id, len(UID_COUNTER) + 1)
    status = "Платный подписчик" if call.from_user.id in PAID_USERS else "Без подписки"
    kb = await back_button()
    await call.message.edit_text(
        f"👤 Ваш профиль\nUID: {uid}\nСтатус: {status}", reply_markup=kb
    )
    await call.answer()

@dp.callback_query(F.data == "subscription")
async def subscription(call):
    user_id = call.from_user.id
    key = f"UID_{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/get_key_info", params={"key": key}) as resp:
            data = await resp.json()
    kb = await back_button()
    if not data.get("found"):
        PAID_USERS.discard(user_id)
        await call.message.edit_text("❌ У вас нет активной подписки.", reply_markup=kb)
    else:
        PAID_USERS.add(user_id)
        await call.message.edit_text(
            f"🔑 Ключ: {data['key']}\n📱 HWID: {data['hwid']}\n🛡️ DLC: {data['dlc_status']}", reply_markup=kb
        )
    await call.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Доступ запрещён", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать ключ", callback_data="create_key")
    kb.button(text="⬅️ Назад", callback_data="back")
    await call.message.edit_text("⚙️ Админ панель", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(F.data == "create_key")
async def create_key_start(call):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Доступ запрещён", show_alert=True)
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/activate_key", params={"code": "admin"}) as resp:
            res = await resp.json()
    kb = await back_button()
    if res.get("success"):
        await call.message.edit_text(f"✅ Ключ создан:\n<code>{res['key']}</code>", parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await call.message.edit_text("❌ Ошибка при создании ключа.", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call):
    is_admin = call.from_user.id in ADMIN_IDS
    kb = await main_menu_keyboard(is_admin)
    await call.message.edit_text("👋 Главное меню", reply_markup=kb)
    await call.answer()

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
