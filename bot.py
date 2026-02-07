# ===============================
# Dears Loyalty Card Telegram Bot
# ===============================
# Этот бот нужен для создания карты лояльности.
# Пользователь нажимает /start, отправляет номер,
# бот сохраняет его в базе и выдает QR-код.
# Если номер уже есть — QR повторно не создается.

import os
import psycopg2
import qrcode
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===============================
# Я беру токен бота из Railway Variables
# ===============================
TOKEN = os.getenv("8535698958:AAEBKxx6xCYE0kT5ca0t9KH-_1uZwZaHets")

# ===============================
# Я использую DATABASE_URL от Railway Postgres
# Это самый надежный способ подключения
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

# ===============================
# Здесь я указываю свой Telegram ID
# Он нужен, чтобы только я видел список клиентов
# ===============================
ADMIN_ID = 1284049287  # ← TELEGRAM ID


# ===============================
# Функция подключения к базе данных
# ===============================
def get_db():
    return psycopg2.connect(DATABASE_URL)


# ===============================
# Создание таблицы, если её еще нет
# ===============================
def init_db():
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


# ===============================
# Команда /start
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Кнопка для отправки номера телефона
    button = KeyboardButton(
        text="📲 Получить карту Dears",
        request_contact=True
    )

    keyboard = ReplyKeyboardMarkup(
        [[button]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "💛 *Dears — карта лояльности*\n\n"
        "Показывайте QR-код на кассе и получайте кэшбек.\n\n"
        "Нажмите кнопку ниже, чтобы получить карту 👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ===============================
# Обработка номера телефона
# ===============================
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Я забираю номер пользователя
    phone = update.message.contact.phone_number
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")

    conn = get_db()
    cur = conn.cursor()

    # Проверяю, есть ли такой номер в базе
    cur.execute("SELECT phone FROM clients WHERE phone = %s", (phone,))
    exists = cur.fetchone()

    if exists:
        text = (
            "ℹ️ *У вас уже есть карта Dears.*\n"
            "Используйте этот QR-код при оплате 👇"
        )
    else:
        # Если номера нет — сохраняю его
        cur.execute(
            "INSERT INTO clients (phone, registered_at) VALUES (%s, %s)",
            (phone, datetime.now())
        )
        conn.commit()

        text = (
            "✅ *Карта Dears успешно создана!*\n"
            "Сохраните QR-код и показывайте его на кассе 💸"
        )

    cur.close()
    conn.close()

    # Генерирую QR-код на основе номера
    img = qrcode.make(phone)
    img.save("qr.png")

    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_photo(
        photo=open("qr.png", "rb"),
        caption="💛 Dears — карта лояльности"
    )


# ===============================
# Команда /clients — список клиентов (только для меня)
# ===============================
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
        await update.message.reply_text("Пока ни один клиент не зарегистрирован.")
        return

    text = "👥 *Клиенты с картой Dears:*\n\n"
    for i, (phone,) in enumerate(rows, start=1):
        text += f"{i}) {phone}\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# ===============================
# Запуск бота
# ===============================
def main():
    # Сначала я инициализирую базу данных
    init_db()

    # Создаю приложение Telegram
    app = Application.builder().token(TOKEN).build()

    # Регистрирую команды и обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clients", clients))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    print("✅ Dears bot is running with PostgreSQL")

    # Запускаю бота
    app.run_polling()


# ===============================
# Точка входа
# ===============================
if __name__ == "__main__":
    main()
