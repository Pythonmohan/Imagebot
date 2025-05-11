import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import base64
from io import BytesIO

# Bot token from env
BOT_TOKEN = os.getenv("BOT_TOKEN")
user_states = {}
pending_images = {}
encoded_data = {}

# Flask dummy app
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Bot is running!"

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to StegoBot!\nUse /encode to hide a message\nUse /decode to extract it."
    )

async def encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_image"
    await update.message.reply_text("📷 Send the image to encode your message into.")

async def get_encode_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_states.get(user_id) != "awaiting_image":
        return

    if not update.message.photo:
        await update.message.reply_text("❗ Send a valid image.")
        return

    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    image_data = await photo_file.download_as_bytearray()
    pending_images[user_id] = image_data
    user_states[user_id] = "awaiting_text"
    await update.message.reply_text("✍️ Now send the hidden text message.")

async def get_hidden_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_states.get(user_id) != "awaiting_text":
        return

    message = update.message.text
    image_data = pending_images.get(user_id)
    if not image_data:
        await update.message.reply_text("⚠️ No image found. Start with /encode.")
        return

    encoded = base64.b64encode(message.encode()).decode()
    encoded_data[user_id] = encoded
    await update.message.reply_text("✅ Message saved! Use /decode to extract it later.")
    user_states.pop(user_id, None)

async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_decode_image"
    await update.message.reply_text("📥 Send the image to decode the hidden message.")

async def get_decode_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_states.get(user_id) != "awaiting_decode_image":
        return

    if not update.message.photo:
        await update.message.reply_text("❗ Send a valid image.")
        return

    hidden = encoded_data.get(user_id)
    if hidden:
        try:
            decoded = base64.b64decode(hidden.encode()).decode()
            await update.message.reply_text(f"🕵️ Hidden message:\n\n{decoded}")
        except:
            await update.message.reply_text("⚠️ Failed to decode message.")
    else:
        await update.message.reply_text("🚫 No hidden message found.")
    user_states.pop(user_id, None)

def run_bot():
    from telegram.ext import Application

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("encode", encode))
    app.add_handler(CommandHandler("decode", decode))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, get_encode_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_hidden_text))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, get_decode_image))

    app.run_polling()

if __name__ == '__main__':
    # Run the Telegram bot in a separate thread
    threading.Thread(target=run_bot).start()

    # Start Flask app to keep Render happy
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
    
