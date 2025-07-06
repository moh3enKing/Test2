import asyncio
import logging
import re
import time
from datetime import datetime
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart
from motor.motor_asyncio import AsyncIOMotorClient
from async_limiter import AsyncLimiter

API_TOKEN = '8089258024:AAFx2ieX_ii_TrI60wNRRY7VaLHEdD3-BP0'
MONGO_URI = 'mongodb+srv://mohsenfeizi1386:RIHPhDJPhd9aNJvC@cluster0.ounkvru.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
CHANNEL_USERNAME = '@netgoris'
OWNER_ID = 5637609683

AI_ENDPOINTS = [
    "https://test1-je97.onrender.com/Ai/index.php?text=",
    "https://test1-je97.onrender.com/Ai/index.php?model=gpt&text=",
    "https://test1-je97.onrender.com/Ai/index.php?model=deepseek&text="
]

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = AsyncIOMotorClient(MONGO_URI)['copilotai']
users_collection = db['users']
spam_limiter = {}
spam_muted_users = {}
chat_limiter = AsyncLimiter(1, 2)

def get_force_join_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ من عضو شدم", callback_data="joined")]
    ])

async def is_user_joined(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@dp.callback_query(F.data == "joined")
async def joined_callback(callback: CallbackQuery):
    if await is_user_joined(callback.from_user.id):
        await callback.message.delete()
        await send_welcome(callback.message)
    else:
        await callback.answer("❌ هنوز عضو نشدی!", show_alert=True)

async def send_welcome(message: Message):
    uid = message.from_user.id
    user_data = await users_collection.find_one({"user_id": uid})
    if not user_data:
        await users_collection.insert_one({"user_id": uid, "joined_at": datetime.now()})
        await bot.send_message(OWNER_ID, f"🤖 کاربر جدید:\n🆔 <code>{uid}</code>\n👤 {message.from_user.full_name}")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📘 راهنما", callback_data="show_help")]
    ])
    await message.answer_sticker("CAACAgUAAxkBAAEB-KRiZcxNa2a-QS4bR2qSmLXrxUqZ9AACmgIAAnVjWFePQ62FgoUpSy8E")
    await message.answer(f"👋 سلام {message.from_user.first_name}!\nخوش اومدی به ربات هوش مصنوعی.\nاز دکمه زیر برای دریافت راهنما استفاده کن.", reply_markup=markup
                        
                    )
  HELP_TEXT = """🧠 <b>راهنمای استفاده از ربات:</b>

✅ امکان گفت‌وگو با هوش مصنوعی، دانلود محتوا، ساخت عکس

🔗 لینک‌های مجاز:
• instagram.com
• spotify.com
• pinterest.com
• image/text=

⚠️ استفاده نادرست = مسدود شدن
📎 برای بازگشت دکمه زیر را بزن"""

@dp.callback_query(F.data == "show_help")
async def show_help(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_home")]
    ])
    await callback.message.edit_text(HELP_TEXT, reply_markup=kb)

@dp.callback_query(F.data == "back_to_home")
async def back_to_home(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📘 راهنما", callback_data="show_help")]
    ])
    await callback.message.edit_text("📍 به منوی اصلی برگشتی", reply_markup=kb)

@dp.message(F.text)
async def handle_text(message: Message):
    uid = message.from_user.id
    now = time.time()

    if uid in spam_muted_users and now < spam_muted_users[uid]:
        return

    recent = spam_limiter.get(uid, [])
    recent = [t for t in recent if now - t < 60]
    recent.append(now)
    spam_limiter[uid] = recent

    if len(recent) >= 4:
        spam_muted_users[uid] = now + 120
        await message.reply("⛔️ اسپم شناسایی شد! تا ۲ دقیقه پاسخ داده نمی‌شه.")
        return

    if not await is_user_joined(uid):
        await message.reply("📢 لطفاً عضو کانال شو", reply_markup=get_force_join_markup())
        return

    if "http" in message.text.lower():
        await handle_links(message)
    else:
        await message.answer_chat_action("typing")
        res = await get_ai_response(message.text)
        await message.reply(res)

async def get_ai_response(text: str):
    for url in AI_ENDPOINTS:
        async with chat_limiter:
            try:
                async with ClientSession() as session:
                    async with session.get(f"{url}{text}") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for key in ["result", "response", "text"]:
                                if key in data:
                                    return data[key]
            except Exception:
                continue
    return "❌ سرورهای هوش مصنوعی قطع هستند."

async def handle_links(message: Message):
    url = message.text.strip()

    if "instagram.com" in url:
        await handle_instagram(url, message)
    elif "spotify.com" in url:
        await handle_spotify(url, message)
    elif "pinterest.com" in url:
        await handle_pinterest(url, message)
    elif "text=" in url.lower():
        await handle_image_generation(url, message)
    else:
        await message.reply("❌ لینک غیرمجاز!")

# هر کدام از این توابع (`handle_instagram`, `handle_spotify`, ...) تو بخش قبل کامل فرستاده شدن


from aiogram.types import ReplyKeyboardRemove

support_sessions = {}

@dp.message(F.text == "💬 پشتیبانی")
async def enter_support(message: Message):
    if message.chat.type != "private":
        return
    support_sessions[message.from_user.id] = True
    await message.reply("📩 پیام خود را ارسال کنید تا ادمین پاسخ دهد.\nبرای خروج /cancel را بزنید.",
                        reply_markup=ReplyKeyboardRemove())

@dp.message(F.text == "/cancel")
async def exit_support(message: Message):
    if message.from_user.id in support_sessions:
        del support_sessions[message.from_user.id]
        kb = ReplyKeyboardMarkup(keyboard=[
            [InlineKeyboardButton("📘 راهنما", callback_data="show_help")],
            [KeyboardButton("💬 پشتیبانی")]
        ], resize_keyboard=True)
        await message.reply("✅ از پشتیبانی خارج شدی.", reply_markup=kb)

@dp.message()
async def support_router(message: Message):
    uid = message.from_user.id
    if support_sessions.get(uid):
        await bot.send_message(OWNER_ID,
            f"📥 پیام جدید از {uid}:\n\n{message.text}")
        await message.reply("✅ پیام شما به ادمین ارسال شد. لطفاً صبر کنید.")

@dp.message(lambda msg: msg.reply_to_message and str(msg.reply_to_message.text).startswith("📥 پیام جدید از"))
async def admin_reply(message: Message):
    try:
        target_id = int(re.search(r"📥 پیام جدید از (\d+):", message.reply_to_message.text).group(1))
        await bot.send_message(target_id, f"🧑‍💼 پاسخ ادمین:\n\n{message.text}")
        await message.reply("✉️ پیام شما ارسال شد.")
    except:
        await message.reply("❌ خطا در ارسال پاسخ")

@dp.message(F.text == "/panel")
async def admin_panel(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📤 ارسال اعلان", callback_data="admin_alert")]
    ])
    await message.reply("🎛 به پنل مدیریت خوش آمدی:", reply_markup=kb)

@dp.callback_query(F.data == "admin_alert")
async def send_alert_prompt(callback: CallbackQuery):
    await callback.message.edit_text("📝 لطفاً پیامی که می‌خوای برای کاربر ارسال بشه رو بنویس (ریپلای نکن فقط متن بفرست).")
    dp.message.register(waiting_for_alert_message)

async def waiting_for_alert_message(message: Message):
    await bot.send_message(message.chat.id, "✅ اعلان در صف ارسال قرار گرفت.")
    # عملیات بعدی مثل مسدودسازی یا هشدار بعدش اجرا می‌تونه شه
    dp.message.unregister(waiting_for_alert_message)
  


