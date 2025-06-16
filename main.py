import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7863135976:AAGlQmvWoPPqKtb9kn6WjgiL96AG0a8EFkw"
API_BASE = "https://elevenx.onrender.com"

ADMIN_IDS = {7899575088, 5361974069}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
UID_COUNTER = {}
PAID_USERS = set()

class KeyInput(StatesGroup):
    waiting_for_key = State()

async def main_menu_keyboard(is_admin=False):
    kb = InlineKeyboardBuilder()
    kb.button(text="ℹ️О Магазине", callback_data="about")
    kb.button(text="✨Моя Подписка", callback_data="subscription")
    kb.button(text="👤Профиль", callback_data="profile")
    if is_admin:
        kb.button(text="⚙️ Админ панель", callback_data="admin_panel")
    return kb.as_markup()

async def back_button(extra_buttons: list[InlineKeyboardButton] = None):
    kb = InlineKeyboardBuilder()
    if extra_buttons:
        for btn in extra_buttons:
            kb.row(btn)
    kb.button(text="⬅️ Назад", callback_data="back")
    return kb.as_markup()

@dp.message(CommandStart(deep_link=True))
async def activate_command(msg, command: CommandStart):
    code = command.args
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/ZJEfYIMk_activate_key",
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
    is_admin = msg.from_user.id in ADMIN_IDS
    keyboard = await main_menu_keyboard(is_admin)
    await msg.answer("👋 Добро пожаловать в бота eLevenX Shop!", reply_markup=keyboard)

@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
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
async def profile(call: CallbackQuery):
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
async def subscription(call: CallbackQuery):
    user_id = call.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/moASnrwD_get_key_info",
            params={"key": f"UID_{user_id}"}
        ) as resp:
            data = await resp.json()
    extra = [InlineKeyboardButton(text="🔓 Активировать ключ", callback_data="activate_key")]
    kb = await back_button(extra_buttons=extra)
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

@dp.callback_query(F.data == "activate_key")
async def ask_key(call: CallbackQuery, state: FSMContext):
    await state.set_state(KeyInput.waiting_for_key)
    await call.message.edit_text("🔐 Введите ключ, который вы хотите активировать:")
    await call.answer()

@dp.message(StateFilter(KeyInput.waiting_for_key))
async def process_key_input(msg: Message, state: FSMContext):
    key = msg.text.strip()
    hwid = f"UID_{msg.from_user.id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/TKVYLeXu_check", params={"key": key, "hwid": hwid}) as resp:
            res = await resp.json()
    await state.clear()
    if res.get("valid"):
        PAID_USERS.add(msg.from_user.id)
        await msg.answer("✅ Ключ успешно активирован и привязан к вашему Telegram!")
    else:
        await msg.answer("❌ Неверный или уже использованный ключ.")

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Доступ запрещён", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать ключ", callback_data="create_key")
    kb.button(text="⬅️ Назад", callback_data="back")
    await call.message.edit_text("⚙️ Админ панель", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(F.data == "create_key")
async def create_key_start(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Доступ запрещён", show_alert=True)
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/generate_key") as resp:
            res = await resp.json()
    kb = await back_button()
    if res.get("success") and res.get("key"):
        await call.message.edit_text(f"✅ Ключ создан:\n<code>{res['key']}</code>", parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await call.message.edit_text("❌ Ошибка при создании ключа.", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    is_admin = call.from_user.id in ADMIN_IDS
    keyboard = await main_menu_keyboard(is_admin)
    await call.message.edit_text("👋 Добро пожаловать в бота eLevenX Shop!", reply_markup=keyboard)
    await call.answer()

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
