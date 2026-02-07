import os
import time
import psycopg2
import qrcode
import csv
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8535698958:AAEBKxx6xCYE0kT5ca0t9KH-_1uZwZaHets"
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = 1284049287

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    retries = 5
    delay = 3
    for _ in range(retries):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    phone TEXT PRIMARY KEY,
                    registered_at TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            time.sleep(delay)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Это *Dears — карта лояльности* 💛\n\n"
        "Нажми кнопку ниже, отправь номер\n"
        "и получи QR-код для кэшбека.",
        parse_mode="Markdown"
    )

    button = KeyboardButton(
        text="📲 Получить карту Dears",
        request_contact=True
    )
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    await update.message.reply_text(
        "👇 Получить карту",
        reply_markup=keyboard
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT phone FROM clients WHERE phone = %s", (phone,))
    exists = cur.fetchone()

    if exists:
        text = (
            "ℹ️ *У тебя уже есть карта Dears.*\n\n"
            "Покажи этот QR на кассе 👇"
        )
    else:
        cur.execute(
            "INSERT INTO clients (phone, registered_at) VALUES (%s, %s)",
            (phone, datetime.now())
        )
        conn.commit()
        text = (
            "✅ *Карта Dears создана!*\n\n"
            "Сохрани QR и показывай его на кассе 💸"
        )

    cur.close()
    conn.close()

    img = qrcode.make(phone)
    img.save("qr.png")

    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_photo(
        photo=open("qr.png", "rb"),
        caption="💛 Dears — карта лояльности"
    )

async def clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT phone FROM clients ORDER BY registered_at")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("Пока нет клиентов")
        return

    text = "👥 Клиенты Dears:\n\n"
    for i, (phone,) in enumerate(rows, start=1):
        text += f"{i}) {phone}\n"

    await update.message.reply_text(text)

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT phone, registered_at FROM clients ORDER BY registered_at")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("Нет данных для экспорта")
        return

    filename = "clients.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["phone", "registered_at"])
        for phone, registered_at in rows:
            writer.writerow([phone, registered_at])

    await update.message.reply_document(
        document=open(filename, "rb"),
        caption="📊 Клиенты Dears (CSV)"
    )

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clients", clients))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    print("BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
