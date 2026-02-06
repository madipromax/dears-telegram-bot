import os
import json
import qrcode
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ====== НАСТРОЙКИ ======

# Токен берётся из Railway → Variables
TOKEN = os.getenv("8535698958:AAEBKxx6xCYE0kT5ca0t9KH-_1uZwZaHets")

# МОЙ TELEGRAM ID
ADMIN_ID = 1284049287

DATA_FILE = "users.json"
QR_DIR = "qr"

os.makedirs(QR_DIR, exist_ok=True)

# ====== ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ ======

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ====== /start ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton(
        "📲 Получить карту Dears",
        request_contact=True
    )
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    await update.message.reply_text(
        "💛 *Dears — карта лояльности*\n\n"
        "Получайте кэшбек за каждый заказ.\n\n"
        "📌 *Как это работает:*\n"
        "• покажите QR на кассе\n"
        "• получайте бонусы автоматически\n\n"
        "Нажмите кнопку ниже, чтобы получить карту 👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ====== ОБРАБОТКА НОМЕРА ======

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_phone = update.message.contact.phone_number

    # нормализация номера
    phone = (
        raw_phone
        .replace("+", "")
        .replace(" ", "")
        .replace("-", "")
    )

    qr_path = f"{QR_DIR}/{phone}.png"

    # если карта уже есть
    if phone in users:
        await update.message.reply_text(
            "ℹ️ *У вас уже есть карта Dears.*\n"
            "Используйте этот QR при оплате 👇",
            parse_mode="Markdown"
        )
        await update.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption="📌 Покажите QR на кассе"
        )
        return

    # новая регистрация
    users[phone] = {
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_users()

    img = qrcode.make(phone)
    img.save(qr_path)

    await update.message.reply_text(
        "✅ *Карта Dears создана!*\n\n"
        "Сохраните QR и показывайте его на кассе 💸",
        parse_mode="Markdown"
    )

    await update.message.reply_photo(
        photo=open(qr_path, "rb"),
        caption="💛 Dears — спасибо, что вы с нами"
    )

# ====== /clients (ТОЛЬКО ДЛЯ АДМИНА) ======

async def clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not users:
        await update.message.reply_text("Пока нет зарегистрированных клиентов.")
        return

    text = "👥 *Клиенты с картой:*\n\n"
    for i, phone in enumerate(users.keys(), start=1):
        text += f"{i}) {phone}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ====== ЗАПУСК ======

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clients", clients))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    print("✅ Dears bot is running")
    app.run_polling()

if __name__ == "__main__":
    main()
