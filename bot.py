import sqlite3
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# ==================== SOZLAMALAR ====================
# ⚠️ @BotFather'dan olgan TOKENingizni shu yerga qo'ying (tirnoq ichiga):
TOKEN = "8586560716:AAEpWQeMCe7_slIm3xQO5w9nd99ehu9ZPDE"

# Sizning Telegram ID raqamingiz (Admin sifatida biriktirildi):
ADMIN_ID = 5528462848

# Dialog bosqichlari (Kitob qo'shish uchun)
ADD_PDF, ADD_TITLE, ADD_AUTHOR = range(3)


# ==================== BAZA (DATABASE) ====================
def init_db():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()


# ==================== TUGMALAR ====================
# Oddiy kitobxonlar uchun menyu
USER_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("📚 Barcha kitoblar"), KeyboardButton("🔍 Qidirish")],
    [KeyboardButton("ℹ️ Kutubxona haqida"), KeyboardButton("📞 Aloqa")]
], resize_keyboard=True)

# Admin (Siz) uchun menyu
ADMIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("➕ Yangi kitob qo'shish")],
    [KeyboardButton("📚 Barcha kitoblar"), KeyboardButton("ℹ️ Kutubxona haqida")],
    [KeyboardButton("📞 Aloqa")]
], resize_keyboard=True)


# ==================== /START BUYRUG'I ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Agar siz (Admin) kirsangiz
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👑 **Xush kelibsiz, Bosh Admin!**\n\n"
            "Bu yerdan yangi PDF kitoblarni bazaga qo'shishingiz va botni boshqarishingiz mumkin.",
            reply_markup=ADMIN_MENU,
            parse_mode="Markdown"
        )
    # Oddiy foydalanuvchi kirsa
    else:
        await update.message.reply_text(
            "Assalomu alaykum! Kutubxonamiz rasmiy botiga xush kelibsiz.\n"
            "Bu yerda mualliflik huquqidan o'tgan ochiq PDF kitoblarni tekinga yuklab olishingiz mumkin. 👇",
            reply_markup=USER_MENU
        )


# ==================== KITOB QO'SHISH (ADMIN DIALOGI) ====================
async def start_add_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    
    await update.message.reply_text("📥 Iltimos, kitobning **PDF faylini** botga yuboring:")
    return ADD_PDF

async def get_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document or not update.message.document.mime_type.endswith('pdf'):
        await update.message.reply_text("⚠️ Iltimos, faqat PDF formatidagi fayl yuboring!")
        return ADD_PDF

    context.user_data['file_id'] = update.message.document.file_id
    await update.message.reply_text("✅ PDF qabul qilindi.\n\nEndi **kitob nomini** yozib yuboring:")
    return ADD_TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Endi **muallif ismini** yozib yuboring:")
    return ADD_AUTHOR

async def get_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    title = context.user_data['title']
    file_id = context.user_data['file_id']

    # Bazaga saqlash
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (file_id, title, author) VALUES (?, ?, ?)", (file_id, title, author))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🎉 **Kitob muvaffaqiyatli saqlandi!**\n\n📖 **Kitob:** {title}\n✍️ **Muallif:** {author}",
        reply_markup=ADMIN_MENU,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=ADMIN_MENU)
    return ConversationHandler.END


# ==================== KITOB KORISH VA YUKLASH ====================
async def show_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author FROM books ORDER BY id DESC")
    books = cursor.fetchall()
    conn.close()

    if not books:
        await update.message.reply_text("Hozircha bazada kitoblar yo'q.")
        return

    keyboard = []
    for book_id, title, author in books:
        keyboard.append([InlineKeyboardButton(f"📖 {title} - {author}", callback_data=f"book_{book_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Mavjud kitoblar ro'yxati (Yuklab olish uchun bosing):", reply_markup=reply_markup)

# Tugma bosilganda PDF faylni yuborish
async def send_pdf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    book_id = query.data.split("_")[1]

    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, title, author FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()

    if book:
        file_id, title, author = book
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_id,
            caption=f"📚 **{title}**\n✍️ *{author}*\n\n✅ Ko'kdala tuman AKM kutubxonasi boti orqali yuklab olindi.",
            parse_mode="Markdown"
        )
    else:
        await query.message.reply_text("⚠️ Kechirasiz, kitob topilmadi.")


# ==================== MATNLI XABARLAR ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Barcha kitoblar":
        await show_books(update, context)
    elif text == "ℹ️ Kutubxona haqida":
        await update.message.reply_text(
            "🏢 **Ko'kdala tuman AKM**\n\n"
            "Kutubxonamizda ochiq foydalanishdagi barcha huquqi o'tgan adabiyotlarni topishingiz mumkin.",
            parse_mode="Markdown"
        )
    elif text == "📞 Aloqa":
        await update.message.reply_text(
            "📍 **Manzil:** Ko‘kdala tumani, Oltin dala MFY, Nurafshon ko‘chasi, 43-uy\n"
            "👨‍💻 **Admin:** @yuldoshev02",
            parse_mode="Markdown"
        )
    elif text == "🔍 Qidirish":
        await update.message.reply_text("Qidiruv bo'limi tez orada ishga tushadi.")


# ==================== ASOSIY ISHGA TUSHIRISH ====================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Admin kitob qo'shish dialogi
    add_book_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Yangi kitob qo'shish$"), start_add_book)],
        states={
            ADD_PDF: [MessageHandler(filters.Document.ALL, get_pdf)],
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            ADD_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_author)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_book_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(send_pdf_file, pattern="^book_"))

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()
