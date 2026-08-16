import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8601799589:AAGHky10R-1PwO6iPymp5pdZNQVoQtaLotg"
user_links = {} # نخزن الرابط مؤقتا

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 ارسل لي رابط تغريدة X فيها فيديو")

async def get_video_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "x.com" not in url and "twitter.com" not in url:
        await update.message.reply_text("🚫 هذا الرابط غير مدعوم. ارسل رابط X فقط")
        return

    msg = await update.message.reply_text("⏳ جاري استخراج الجودات المتاحة...")

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        # نخزن الرابط باسم المستخدم
        user_links[update.message.chat_id] = url

        # نجيب الجودات المتاحة ونشيل 1080
        formats = []
        for f in info.get('formats', []):
            if f.get('height') and f.get('ext') == 'mp4':
                h = f['height']
                if h in [360, 480, 720]: # شلنا 1080
                    size = f.get('filesize', 0) / 1024 / 1024
                    formats.append([f"{h}p - {size:.1f}MB", str(f['format_id'])])

        # لو ما لقينا شي نعطيه 360 اجباري
        if not formats:
            formats = [["360p", "best[height<=360]"]]

        # نشيل التكرار
        formats = list(dict.fromkeys([tuple(x) for x in formats]))

        keyboard = [[InlineKeyboardButton(text, callback_data=data)] for text, data in formats[:5]] # 5 ازرار بس

        await msg.edit_text(
            f"🔍 لقينا {len(formats)} جودة للفيديو:\n{info.get('title', '')[:50]}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await msg.edit_text(f"🚫 صار خطأ: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ جاري التحميل... 0%")

    chat_id = query.message.chat_id
    url = user_links.get(chat_id)
    format_id = query.data

    status_msg = await context.bot.send_message(chat_id, "📊 التحميل بدأ...")

    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            try:
                context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"📊 جاري التحميل: {p}")
            except: pass

    ydl_opts = {
        'format': format_id,
        'outtmpl': '%(title).50s.%(ext)s',
        'progress_hooks': [progress_hook],
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await status_msg.edit_text("📤 جاري الرفع...")
        await context.bot.send_video(chat_id, video=open(filename, 'rb'), caption="✅ تم")
        os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"🚫 فشل التحميل: {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_video_info))
app.add_handler(CallbackQueryHandler(button_handler))
app.run_polling()