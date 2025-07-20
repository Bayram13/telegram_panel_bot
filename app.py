import json, os
from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telegram.Bot(token=TOKEN)

# JSON database helper
def load_db():
    with open("database.json", "r") as f:
        return json.load(f)

def save_db(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=2)

def get_balance(user_id):
    db = load_db()
    return db.get(str(user_id), {}).get("balance", 0)

def set_balance(user_id, balance):
    db = load_db()
    db.setdefault(str(user_id), {})["balance"] = balance
    save_db(db)

# Telegram webhook endpoint
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Start handler
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("💰 Balans artır", callback_data='balans_artir')],
        [InlineKeyboardButton("📊 Balansa baxmaq", callback_data='balans_bax')],
        [InlineKeyboardButton("🛒 Xidmətlər", callback_data='xidmetler')],
        [InlineKeyboardButton("📩 Adminlə əlaqə", url="https://t.me/bayr4m")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Salam! Aşağıdakı menyudan seçim edin:", reply_markup=reply_markup)

# Callback handlers
def button(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == "balans_artir":
        keyboard = [[InlineKeyboardButton("✅ Ödənildi", callback_data='odenildi')]]
        text = "Kapital Bank: `12345678`\nLeobank: `87654321`\n\nÖdəniş etdikdən sonra çek şəklini göndərin və 'Ödənildi' düyməsini seçin."
        query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "odenildi":
        bot.send_message(chat_id=user_id, text="Zəhmət olmasa çek şəklini bu mesaja cavab olaraq göndərin.")

    elif query.data == "balans_bax":
        balans = get_balance(user_id)
        query.edit_message_text(text=f"📊 Cari balansınız: {balans} AZN")

    elif query.data == "xidmetler":
        xidmetler = [
            [InlineKeyboardButton("🎵 TikTok", callback_data="xid_tiktok")],
            [InlineKeyboardButton("📸 Instagram", callback_data="xid_instagram")],
            [InlineKeyboardButton("📢 Telegram", callback_data="xid_telegram")]
        ]
        query.edit_message_text("Xidmətlərdən birini seçin:", reply_markup=InlineKeyboardMarkup(xidmetler))

# Admin /add
def admin_add(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        _, user_id, amount = update.message.text.split()
        user_id, amount = int(user_id), float(amount)
        old = get_balance(user_id)
        set_balance(user_id, old + amount)
        bot.send_message(chat_id=user_id, text=f"✅ Ödəniş təsdiqləndi.\n{amount} AZN əlavə olundu. Yeni balans: {old + amount} AZN")
        update.message.reply_text("Balans artırıldı.")
    except:
        update.message.reply_text("İstifadə: /add <id> <məbləğ>")

# Çek şəkli adminə
def cek_handler(update, context):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        caption = f"Yeni çek! İstifadəçi ID: {update.message.from_user.id}"
        bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption)

# Dispatcher
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("add", admin_add))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.photo, cek_handler))
