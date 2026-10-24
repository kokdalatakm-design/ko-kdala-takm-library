import http.server
import os
import sqlite3
import threading
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ================= SOZLAMALAR =================
TOKEN = "8586560716:AAGJdMpGVLLsuQrMPWKWqFxMB6ZqeFMHw2o"
ADMIN_ID = 5528462848

ADD_PDF, ADD_TITLE, ADD_AUTHOR = range(3)


# --- RENDER UCHUN VEB SERVER (PORT XATOSINI OLDINI OLISH) ---
def run_http_server():
  port = int(os.environ.get("PORT", 10000))
  server_address = ("", port)
  httpd = http.server.HTTPServer(
      server_address, http.server.SimpleHTTPRequestHandler
  )
  httpd.serve_forever()


# Veb-serverni alohida oqimda ishga tushiramiz
threading.Thread(target=run_http_server, daemon=True).start()


# ================= MA'LUMOTLAR BAZASI =================
def init_db():
  conn = sqlite3.connect("library.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            file_id TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


# ================= MENYU TUGMALARI =================
def main_keyboard(user_id):
  keyboard = [
      [KeyboardButton("📚 Barcha kitoblar")],
      [
          KeyboardButton("ℹ️ Kutubxona haqida"),
          KeyboardButton("🌐 Ijtimoiy tarmoqlar"),
      ],
      [KeyboardButton("📞 Aloqa")],
  ]
  if user_id == ADMIN_ID:
    keyboard.insert(0, [KeyboardButton("➕ Yangi kitob qo'shish")])

  return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ================= BUYRUQLAR =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  if user_id == ADMIN_ID:
    text = (
        "👑 **Xush kelibsiz, Bosh Admin!**\n\n"
        "Bu yerdan yangi PDF kitoblarni bazaga qo'shishingiz va botni"
        " boshqarishingiz mumkin."
    )
  else:
    text = (
        "📚 **Ko'kdala tuman axborot-kutubxona markazining rasmiy botiga xush"
        " kelibsiz!**\n\nKerakli bo'limni tanlang:"
    )

  await update.message.reply_text(
      text, reply_markup=main_keyboard(user_id), parse_mode="Markdown"
  )


async def ijtimoiy_tarmoqlar(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  keyboard = [
      [
          InlineKeyboardButton(
              "📷 Instagram",
              url=(
                  "https://www.instagram.com/kokdala_takm_?rpxt=MXE4MGNlbnVobGs4bA=="
              ),
          )
      ],
      [
          InlineKeyboardButton(
              "✈️ Telegram kanal",
              url="https://t.me/Kukdalaaxborotkutubxonamarkazi",
          )
      ],
      [
          InlineKeyboardButton(
              "👥 Telegram guruh", url="https://t.me/+ULmvcu0CB4owMjQy"
          )
      ],
      [
          InlineKeyboardButton(
              "📘 Facebook",
              url="https://www.facebook.com/share/1FRMC3XvyA/",
          )
      ],
      [
          InlineKeyboardButton("🐦 Twitter (X)", url="https://x.com/KokdalaTAKM"),
      ],
      [
          InlineKeyboardButton(
              "🎬 YouTube", url="https://www.youtube.com/@KokdalaTAKM-t2v"
          )
      ],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
      "📚 **Ko'kdala tuman axborot-kutubxona markazi**\n\nBizning rasmiy"
      " sahifalarimiz va tarmoqlardagi sahifalarimiz bilan tanishing:",
      reply_markup=reply_markup,
      parse_mode="Markdown",
  )


async def kutubxona_haqida(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  text = (
      "📖 **Ko'kdala tuman axborot-kutubxona markazi**\n\nAholiga va yoshlarga"
      " zamonaviy axborot-kutubxona xizmatlarini ko'rsatish, kitobxonlik"
      " madaniyatini oshirish va boy kitob fondidan foydalanish imkoniyatini"
      " beradi."
  )
  await update.message.reply_text(text, parse_mode="Markdown")


async def aloqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = (
      "📞 **Aloqa va Murojaat:**\n\n📍 Unvon: Ko'kdala tumani\n📧 Email:"
      " kokdalatakm@gmail.com\n🤖 Bot administratoriga murojaat qilish uchun"
      " rasmiy kanallarimizdan foydalaning."
  )
  await update.message.reply_text(text, parse_mode="Markdown")


async def barcha_kitoblar(update: Update, context: ContextTypes.DEFAULT_TYPE):
  conn = sqlite3.connect("library.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, title, author FROM books")
  books = cursor.fetchall()
  conn.close()

  if not books:
    await update.message.reply_text("Hozircha bazada kitoblar yo'q.")
    return

  keyboard = []
  for b_id, title, author in books:
    keyboard.append(
        [
            InlineKeyboardButton(
                f"📖 {title} - {author}", callback_data=f"book_{b_id}"
            )
        ]
    )

  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
      "📚 **Mavjud kitoblar ro'yxati:**\nYuklab olish uchun kitob ustiga"
      " bosing:",
      reply_markup=reply_markup,
      parse_mode="Markdown",
  )


async def send_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  book_id = query.data.split("_")[1]

  conn = sqlite3.connect("library.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT title, author, file_id FROM books WHERE id = ?", (book_id,)
  )
  book = cursor.fetchone()
  conn.close()

  if book:
    title, author, file_id = book
    await query.message.reply_document(
        document=file_id, caption=f"📖 **{title}**\n✍️ {author}"
    )
  else:
    await query.message.reply_text("Kechirasiz, kitob topilmadi.")


# ================= KITOB QO'SHISH (ADMIN) =================
async def start_add_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return ConversationHandler.END

  await update.message.reply_text(
      "📥 Iltimos, kitobning **PDF faylini** yuboring:"
  )
  return ADD_PDF


async def get_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message.document:
    await update.message.reply_text("Iltimos, faqat PDF fayl yuboring!")
    return ADD_PDF

  context.user_data["file_id"] = update.message.document.file_id
  await update.message.reply_text("✍️ Kitob **nomini** kiriting:")
  return ADD_TITLE


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data["title"] = update.message.text
  await update.message.reply_text("👤 Kitob **muallifini** kiriting:")
  return ADD_AUTHOR


async def get_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
  author = update.message.text
  title = context.user_data["title"]
  file_id = context.user_data["file_id"]

  conn = sqlite3.connect("library.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO books (title, author, file_id) VALUES (?, ?, ?)",
      (title, author, file_id),
  )
  conn.commit()
  conn.close()

  await update.message.reply_text(
      f"✅ **Kitob bazaga muvaffaqiyatli qo'shildi!**\n\n📖 Nom:"
      f" {title}\n✍️ Muallif: {author}",
      reply_markup=main_keyboard(ADMIN_ID),
      parse_mode="Markdown",
  )
  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "Bekor qilindi.", reply_markup=main_keyboard(update.effective_user.id)
  )
  return ConversationHandler.END


# ================= ASOSIY MAIN FUNKSIYA =================
def main():
  application = ApplicationBuilder().token(TOKEN).build()

  conv_handler = ConversationHandler(
      entry_points=[
          MessageHandler(filters.Text("➕ Yangi kitob qo'shish"), start_add_book)
      ],
      states={
          ADD_PDF: [MessageHandler(filters.Document.ALL, get_pdf)],
          ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
          ADD_AUTHOR: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, get_author)
          ],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
  )

  application.add_handler(conv_handler)
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("tarmoqlar", ijtimoiy_tarmoqlar))

  application.add_handler(
      MessageHandler(filters.Text("🌐 Ijtimoiy tarmoqlar"), ijtimoiy_tarmoqlar)
  )
  application.add_handler(
      MessageHandler(filters.Text("📚 Barcha kitoblar"), barcha_kitoblar)
  )
  application.add_handler(
      MessageHandler(filters.Text("ℹ️ Kutubxona haqida"), kutubxona_haqida)
  )
  application.add_handler(MessageHandler(filters.Text("📞 Aloqa"), aloqa))

  application.add_handler(CallbackQueryHandler(send_book, pattern="^book_"))

  print("Bot ishga tushdi...")
  application.run_polling()


if __name__ == "__main__":
  main()
