from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import qrcode
import os
import json
from datetime import datetime

TOKEN = "8535698958:AAEBKxx6xCYE0kT5ca0t9KH-_1uZwZaHets"

DATA_FILE = "users.json"
QR_DIR = "qr"

os.makedirs(QR_DIR, exist_ok=True)

# --- загрузка базы пользователей ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# --- /start ---
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

# --- обработка номера телефона ---
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_phone = update.message.contact.phone_number

    # НОРМАЛИЗАЦИЯ НОМЕРА
    phone = raw_phone.replace("+", "").replace(" ", "").replace("-", "")

    qr_path = f"{QR_DIR}/{phone}.png"

    # --- если пользователь уже есть ---
    if phone in users:
        await update.message.reply_text(
            "ℹ️ *У вас уже есть карта Dears.*\n"
            "Используйте этот QR при оплате 👇",
            parse_mode="Markdown"
        )
        await update.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption="📌 Покажите QR на кассе для начисления кэшбека"
        )
        return

    # --- новая регистрация ---
    users[phone] = {
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_users()

    # --- генерация QR ---
    img = qrcode.make(phone)
    img.save(qr_path)

    await update.message.reply_text(
        "✅ *Карта Dears создана!*\n\n"
        "📌 Сохраните этот QR и показывайте его на кассе.\n"
        "Бонусы начисляются автоматически 💸",
        parse_mode="Markdown"
    )

    await update.message.reply_photo(
        photo=open(qr_path, "rb"),
        caption="💛 Dears — спасибо, что вы с нами"
    )

# --- запуск приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

print("✅ Dears bot is running")
app.run_polling()
