import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# رسالة البداية الاحترافية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""✅ أهلاً بك عزي: {update.effective_user.first_name} VIP

- البوت مخصص للتحميل من جميع المواقع
- يمكنك التنزيل من مواقع متعددة بتنسيقات مختلفة
- والإستماع إليها في أي وقت

المواقع المدعومة:
Youtube, Instagram, Facebook, Twitter, Tiktok, Snapchat, Soundcloud, Pinterest, Likee, Kwai

ارسل الرابط فقط 👇"""
    await update.message.reply_text(text)

# استقبال الرابط
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("⏳ جارِ جلب محتوى X، يرجى الانتظار...")

    try:
        # اهم حاجة عشان ما يجيبش اخطاء: نحدث الكوكيز ونجرب كل الصيغ
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'cookiefile': None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)

        title = info.get('title', 'فيديو')
        duration = info.get('duration', 0)
        dur_str = f"{duration//60}:{(duration%60):02d}" if duration else ""

        # نجيب كل الجودات المتاحة
        keyboard = []
        formats = [f for f in info.get('formats', []) if f.get('vcodec')!= 'none']
        formats = sorted(formats, key=lambda x: x.get('height', 0), reverse=True)[:4] # افضل 4 جودات

        for f in formats:
            height = f.get('height', '??')
            btn = InlineKeyboardButton(f"الجودة {height}p ({dur_str}) 📹", callback_data=f"dl|{url}|{f['format_id']}")
            keyboard.append([btn])

        keyboard.append([InlineKeyboardButton("مشاهدة المنشور الاصلي", url=url)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(f"اختر جودة الفيديو رقم 1 ({dur_str}):\n{title[:100]}", reply_markup=reply_markup)

    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ غير متوقع اثناء معالجة طلب X الخاص بك.\nجرب رابط اخر او بعد 5 دقائق")

# زر التحميل
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحميل...")
    _, url, format_id = query.data.split("|")

    await query.edit_message_text("⏳ تم استلام طلبك بنجاح!\nأنت الآن رقم 1 في قائمة الانتظار.\nسيتم إعلامك فور اكتمال التحميل.")

    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            file = ydl.prepare_filename(info)

        caption = f"X - @{context.bot.username}\n{info.get('title','')}"
        await context.bot.send_video(chat_id=query.message.chat_id, video=open(file, 'rb'), caption=caption)
        os.remove(file)

    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ فشل التحميل. الرابط قد يكون خاص او محذوف")

def main():
    os.makedirs("downloads", exist_ok=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
