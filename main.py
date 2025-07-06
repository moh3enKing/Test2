import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import pymongo
import requests
from datetime import datetime, timedelta
import asyncio
import json
from urllib.parse import urlparse
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.getenv("TOKEN", "8089258024:AAFx2ieX_ii_TrI60wNRRY7VaLHEdD3-BP0")
ADMIN_ID = 5637609683
CHANNEL_ID = "@netgoris"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://mohsenfeizi1386:RIHPhDJPhd9aNJvC@cluster0.ounkvru.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://test1-je97.onrender.com/")

# Web services
AI_SERVICES = [
    "https://starsshoptl.ir/Ai/index.php?text={}",
    "https://starsshoptl.ir/Ai/index.php?model=gpt&text={}",
    "https://starsshoptl.ir/Ai/index.php?model=deepseek&text={}"
]
INSTAGRAM_API = "https://pouriam.top/eyephp/instagram?url={}"
SPOTIFY_API = "http://api.cactus-dev.ir/spotify.php?url={}"
PINTEREST_API = "https://haji.s2025h.space/pin/?url={}&client_key=keyvip"
IMAGE_API = "https://v3.api-free.ir/image/?text={}"

# MongoDB setup
client = pymongo.MongoClient(MONGODB_URI)
db = client["telegram_bot"]
users_collection = db["users"]

# Spam protection
SPAM_LIMIT = 4
SPAM_WINDOW = 120  # seconds (2 minutes)

# Keyboards
MAIN_KEYBOARD = ReplyKeyboardMarkup([["راهنما 📖", "پشتیبانی 🛠"]], resize_keyboard=True)
SUPPORT_CANCEL_KEYBOARD = ReplyKeyboardMarkup([["لغو 🚫"]], resize_keyboard=True)
ADMIN_KEYBOARD = ReplyKeyboardMarkup([["بن کاربر 🚫", "آنبن کاربر ✅", "ارسال پیام 📩"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})

    # Notify admin for first-time users
    if not user:
        users_collection.insert_one({"user_id": user_id, "joined": False, "messages": [], "support_mode": False, "banned": False})
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"کاربر جدید استارت کرد:\nID: {user_id}\nUsername: @{update.effective_user.username or 'None'}"
        )

    # Check if user is banned
    if user and user.get("banned", False):
        await update.message.reply_text("⛔ شما از ربات بن شدی! برای اطلاعات بیشتر با پشتیبانی تماس بگیر.")
        return

    # Check if user has joined the channel
    if not await check_channel_membership(context, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 جوین کانال", url=f"https://t.me/netgoris")],
            [InlineKeyboardButton("✅ تأیید", callback_data="check_join")]
        ])
        await update.message.reply_text(
            "لطفاً برای استفاده از ربات، ابتدا در کانال ما جوین کنید!",
            reply_markup=keyboard
        )
        return

    # Welcome message
    welcome_text = (
        "🎉 به ربات ما خوش اومدی!\n"
        "ممنون که جوین کردی! 😊 حالا می‌تونی از امکانات ربات استفاده کنی.\n"
        "برای اطلاعات بیشتر، دکمه راهنما رو بزن."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_KEYBOARD)

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except telegram.error.TelegramError as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    if await check_channel_membership(context, user_id):
        users_collection.update_one({"user_id": user_id}, {"$set": {"joined": True}})
        welcome_text = (
            "🎉 به ربات ما خوش اومدی!\n"
            "ممنون که جوین کردی! 😊 حالا می‌تونی از امکانات ربات استفاده کنی.\n"
            "برای اطلاعات بیشتر، دکمه راهنما رو بزن."
        )
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=MAIN_KEYBOARD
        )
    else:
        await query.message.edit_text(
            "❌ هنوز در کانال جوین نکردی!\nلطفاً در کانال جوین کن و دوباره تأیید بزن.",
            reply_markup=query.message.reply_markup
        )

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        await update.message.reply_text("لطفاً اول در کانال جوین کن!")
        return

    guide_text = (
        "📖 **راهنمای استفاده از ربات** 📖\n\n"
        "🎯 **چطور از ربات استفاده کنم؟**\n"
        "این ربات بهت کمک می‌کنه تا محتوای اینستاگرام، اسپاتیفای، پینترست و تصاویر تولید شده با هوش مصنوعی رو دانلود کنی. کافیه لینک یا متن مورد نظرت رو بفرستی!\n\n"
        "🔗 **لینک‌های پشتیبانی‌شده**:\n"
        "- اینستاگرام: لینک پست یا ریل\n"
        "- اسپاتیفای: لینک آهنگ\n"
        "- پینترست: لینک پین\n"
        "- ساخت تصویر: متن دلخواه (مثال: `flower`)\n\n"
        "⚠️ **اخطارها و قوانین**:\n"
        "1. فقط لینک‌های معتبر از سرویس‌های بالا ارسال کن. لینک‌های نامعتبر باعث خطا می‌شن.\n"
        "2. اسپم نکن! حداکثر ۴ پیام در ۲ دقیقه می‌تونی بفرستی.\n"
        "3. در صورت تخلف، ممکنه از ربات بن بشی.\n"
        "4. برای هر مشکلی، از دکمه پشتیبانی استفاده کن.\n\n"
        "😊 **سؤالی داشتی؟** دکمه پشتیبانی رو بزن تا بتونیم باهات در ارتباط باشیم!"
    )
    await update.message.reply_text(guide_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    await update.message.reply_text("🌟 ما همیشه در خدمت شما هستیم!", reply_markup=MAIN_KEYBOARD)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        await update.message.reply_text("لطفاً اول در کانال جوین کن!")
        return

    users_collection.update_one({"user_id": user_id}, {"$set": {"support_mode": True}})
    await update.message.reply_text(
        "🛠 لطفاً پیامت رو برای پشتیبانی بفرست یا برای خروج 'لغو' رو بزن.",
        reply_markup=SUPPORT_CANCEL_KEYBOARD
    )

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"support_mode": False}})
    await update.message.reply_text(
        "🚫 پشتیبانی لغو شد. حالا می‌تونی از ربات استفاده کنی!",
        reply_markup=MAIN_KEYBOARD
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ این دستور فقط برای ادمینه!")
        return
    await update.message.reply_text("پنل ادمین 🛠\nلطفاً یه گزینه انتخاب کن:", reply_markup=ADMIN_KEYBOARD)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    user = users_collection.find_one({"user_id": user_id})

    if not user or not user.get("joined", False):
        await update.message.reply_text("لطفاً اول در کانال جوین کن!")
        return

    if user.get("banned", False):
        await update.message.reply_text("⛔ شما از ربات بن شدی! برای اطلاعات بیشتر با پشتیبانی تماس بگیر.")
        return

    # Handle support mode
    if user.get("support_mode", False):
        if message == "لغو":
            await cancel_support(update, context)
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📩 پیام پشتیبانی از @{update.effective_user.username or 'None'} (ID: {user_id}):\n{message}",
                reply_to_message_id=update.message.message_id
            )
            await update.message.reply_text("✅ پیامت به پشتیبانی ارسال شد. منتظر جواب باش!")
        return

    # Spam protection
    now = datetime.now()
    messages = user.get("messages", [])
    messages = [ts for ts in messages if (now - datetime.fromisoformat(ts)).total_seconds() < SPAM_WINDOW]
    messages.append(now.isoformat())
    if len(messages) > SPAM_LIMIT:
        await update.message.reply_text("⛔ لطفاً صبر کن! بیش از حد پیام فرستادی. ۲ دقیقه دیگه امتحان کن.")
        return
    users_collection.update_one({"user_id": user_id}, {"$set": {"messages": messages}})

    # Handle admin commands
    if user_id == ADMIN_ID:
        if message in ["بن کاربر 🚫", "آنبن کاربر ✅", "ارسال پیام 📩"]:
            context.user_data["admin_action"] = message
            await update.message.reply_text("لطفاً آیدی عددی کاربر رو بفرست:")
            return
        elif "admin_action" in context.user_data:
            target_user_id = message.strip()
            if not target_user_id.isdigit():
                await update.message.reply_text("لطفاً یه آیدی عددی معتبر بفرست!")
                return
            target_user_id = int(target_user_id)
            action = context.user_data.pop("admin_action")
            await update.message.reply_text("لطفاً پیام اطلاع‌رسانی به کاربر رو بفرست:")
            context.user_data["admin_action_data"] = {"action": action, "target_user_id": target_user_id}
            return
        elif "admin_action_data" in context.user_data:
            action_data = context.user_data.pop("admin_action_data")
            action = action_data["action"]
            target_user_id = action_data["target_user_id"]
            notification = message

            if action == "بن کاربر 🚫":
                users_collection.update_one({"user_id": target_user_id}, {"$set": {"banned": True}})
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"⛔ شما بن شدی!\nدلیل: {notification}"
                )
                await update.message.reply_text("کاربر با موفقیت بن شد!")
            elif action == "آنبن کاربر ✅":
                users_collection.update_one({"user_id": target_user_id}, {"$set": {"banned": False}})
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✅ بن شما برداشته شد!\nپیام ادمین: {notification}"
                )
                await update.message.reply_text("کاربر با موفقیت آنبن شد!")
            elif action == "ارسال پیام 📩":
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📩 پیام از ادمین:\n{notification}"
                )
                await update.message.reply_text("پیام با موفقیت ارسال شد!")
            return

    # Handle web services
    if "instagram.com" in message:
        await handle_instagram(update, context, message)
    elif "spotify.com" in message:
        await handle_spotify(update, context, message)
    elif "pinterest.com" in message:
        await handle_pinterest(update, context, message)
    else:
        await handle_ai_or_image(update, context, message)

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        response = requests.get(INSTAGRAM_API.format(url))
        if response.status_code != 200:
            await update.message.reply_text("❌ خطا در ارتباط با سرور اینستاگرام. لطفاً بعداً امتحان کن.")
            return
        data = response.json()
        if "links" in data:
            for link in data["links"]:
                if link.endswith(".mp4"):
                    await update.message.reply_video(video=link)
                elif link.endswith((".jpg", ".png")):
                    await update.message.reply_photo(photo=link)
        else:
            await update.message.reply_text("❌ خطا: هیچ رسانه‌ای پیدا نشد!")
    except Exception as e:
        logger.error(f"Error processing Instagram link: {e}")
        await update.message.reply_text(f"❌ خطا در پردازش لینک اینستاگرام: {str(e)}")

async def handle_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        response = requests.get(SPOTIFY_API.format(url))
        if response.status_code != 200:
            await update.message.reply_text("❌ خطا در ارتباط با سرور اسپاتیفای. لطفاً بعداً امتحان کن.")
            return
        data = response.json()
        if data.get("ok") and "data" in data and "download_url" in data["data"]["track"]:
            await update.message.reply_audio(audio=data["data"]["track"]["download_url"])
        else:
            await update.message.reply_text("❌ خطا: هیچ آهنگی پیدا نشد!")
    except Exception as e:
        logger.error(f"Error processing Spotify link: {e}")
        await update.message.reply_text(f"❌ خطا در پردازش لینک اسپاتیفای: {str(e)}")

async def handle_pinterest(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        response = requests.get(PINTEREST_API.format(url))
        if response.status_code != 200:
            await update.message.reply_text("❌ خطا در ارتباط با سرور پینترست. لطفاً بعداً امتحان کن.")
            return
        data = response.json()
        if data.get("status") and "download_url" in data:
            await update.message.reply_photo(photo=data["download_url"])
        else:
            await update.message.reply_text("❌ خطا: هیچ تصویری پیدا نشد!")
    except Exception as e:
        logger.error(f"Error processing Pinterest link: {e}")
        await update.message.reply_text(f"❌ خطا در پردازش لینک پینترست: {str(e)}")

async def handle_ai_or_image(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # Try AI services
    for api in AI_SERVICES:
        try:
            response = requests.get(api.format(text))
            if response.status_code == 200:
                await update.message.reply_text(response.text)
                return
        except Exception as e:
            logger.error(f"Error processing AI service {api}: {e}")
            continue

    # If AI fails, try image generation
    try:
        response = requests.get(IMAGE_API.format(text))
        if response.status_code != 200:
            await update.message.reply_text("❌ خطا در ارتباط با سرور ساخت تصویر. لطفاً بعداً امتحان کن.")
            return
        data = response.json()
        if data.get("ok") and "result" in data:
            await update.message.reply_photo(photo=data["result"])
        else:
            await update.message.reply_text("❌ خطا: هیچ تصویری تولید نشد!")
    except Exception as e:
        logger.error(f"Error processing image generation: {e}")
        await update.message.reply_text(f"❌ خطا در پردازش درخواست: {str(e)}")

async def main():
    # Initialize the application
    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.Regex("راهنما 📖"), guide))
    app.add_handler(MessageHandler(filters.Regex("پشتیبانی 🛠"), support))
    app.add_handler(MessageHandler(filters.Regex("لغو 🚫"), cancel_support))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))

    # Start webhook with proper event loop handling
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8443)),
            url_path="/",
            webhook_url=WEBHOOK_URL
        )
        logger.info("Webhook started successfully")
        # Keep the application running
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Error starting webhook: {e}")
        raise
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
