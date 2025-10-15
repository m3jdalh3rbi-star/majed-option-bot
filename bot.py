
import os
import json
import logging
import imghdr
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("majed-bot")

# ---------- Config ----------
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

DISPLAY_NAME        = CFG.get("DISPLAY_NAME", "majed")
PREMIUM_CHANNEL_ID  = CFG.get("PREMIUM_CHANNEL_ID")   # e.g. "@yourchannel" or numeric id
SALLA_URL           = CFG.get("SALLA_URL")
ADMIN_USER_ID       = int(CFG.get("ADMIN_USER_ID", 0))
WATERMARK_ENABLED   = bool(CFG.get("WATERMARK_ENABLED", True))
WATERMARK_FILE      = CFG.get("WATERMARK_FILE", "assets/MajedRobotWatermark.png")
TZ                  = ZoneInfo(CFG.get("TIMEZONE","Asia/Riyadh"))

BOT_TOKEN = os.getenv("BOT_TOKEN")  # put token in Replit Secrets

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing. Add it in Replit Secrets.")

# ---------- Helpers ----------

def is_admin(user_id: int) -> bool:
    return ADMIN_USER_ID != 0 and user_id == ADMIN_USER_ID

def brand_caption(lines: list[str]) -> str:
    stamp = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    header = f"🔥 {DISPLAY_NAME} — SPX/Options Bot\n"
    footer = f"\n—\n⏱️ {stamp} ({CFG.get('TIMEZONE')})\n⚠️ التداول مسؤوليتك الشخصية"
    return header + "\n".join(lines) + footer

def sub_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("اشترك الآن عبر Salla", url=SALLA_URL)]])

async def send_to_channel(context: ContextTypes.DEFAULT_TYPE, photo_file_id: str|None, caption: str):
    if photo_file_id:
        await context.bot.send_photo(chat_id=PREMIUM_CHANNEL_ID, photo=photo_file_id, caption=caption, reply_markup=sub_keyboard())
    else:
        await context.bot.send_message(chat_id=PREMIUM_CHANNEL_ID, text=caption, reply_markup=sub_keyboard())

# ---------- Commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"أهلًا بك في {DISPLAY_NAME} 🤖\n"
        "بوت تنبيهات عقود SPX/QQQ و أسهم الذكاء الاصطناعي.\n\n"
        "للاشتراك في القناة الخاصة: اضغط الزر بالأسفل.",
        reply_markup=sub_keyboard()
    )

async def setadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin bootstrap: first time set ADMIN_USER_ID by editing config.json manually.
       This command only confirms your ID and admin status."""
    uid = update.effective_user.id
    txt = f"🔐 Your user id is: {uid}\n"
    if is_admin(uid):
        txt += "✅ Admin verified."
    else:
        txt += "❌ Not admin. ضع رقمك في ADMIN_USER_ID داخل config.json ثم أعد التشغيل."
    await update.message.reply_text(txt)

async def newpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only. Usage:
       - Reply to a photo with: /newpost دخول PUT على SPX 5700 بسعر 3.10 هدف +30%
       - Or without photo: /newpost تنبيه: فرصة دخول QQQ Calls عند اختراق 480
    """
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("❌ الأمر للمشرف فقط.")
    text = " ".join(context.args) if context.args else "تنبيه صفقة جديدة"
    caption = brand_caption([text])

    # If this command is a reply to a photo, reuse that media
    photo_file_id = None
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        # highest resolution photo is last
        photo = update.message.reply_to_message.photo[-1]
        photo_file_id = photo.file_id

    await send_to_channel(context, photo_file_id, caption)
    await update.message.reply_text("✅ تم نشر التنبيه في القناة.")

async def update_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only. Usage:
       /update +30% تحقق الهدف الأول
       /update تم تفعيل وقف الخسارة -15%
    """
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("❌ الأمر للمشرف فقط.")
    text = " ".join(context.args) if context.args else "تحديث صفقة"
    caption = brand_caption([f"📊 تحديث: {text}"])
    await send_to_channel(context, None, caption)
    await update.message.reply_text("✅ تم إرسال التحديث.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر المتاحة:\n"
        "/start — رسالة ترحيب وزر الاشتراك\n"
        "/setadmin — يعرض User ID والتأكد من الصلاحية\n"
        "/newpost — (للمشرف) نشر تنبيه صفقة. استخدمه ردًا على صورة لإرسالها للقناة.\n"
        "/update — (للمشرف) إرسال تحديث للصفقة.\n"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setadmin", setadmin))
    app.add_handler(CommandHandler("newpost", newpost))
    app.add_handler(CommandHandler("update", update_trade))

    # optional: echo message filter for debugging
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, start))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
