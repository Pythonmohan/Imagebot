import os
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import logging
import base64

# Load .env if running locally
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# In-memory "database"
user_states = {}
pending_images = {}
encoded_data = {}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to StegoBot!\n\n"
        "Use /encode to hide a message in an image.\n"
        "Use /decode to extract a hidden message."
    )


async def encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_image"
    await update.message.reply_text("📷 Please send the image you want to encode your message into.")


async def get_encode_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_states.get(user_id) != "awaiting_image":
        return

    if not update.message.photo:
        await update.message.reply_text("❗ Please send a valid image.")
        return

    # Get image file
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    image_data = await photo_file.download_as_bytearray()

    pending_images[user_id] = image_data
    user_states[user_id] = "awaiting_text"
    await update.message.reply_text("✍️ Now send the hidden text message you want to encode.")


async def get_hidden_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_states.get(user_id) != "awaiting_text":
        return

    message = update.message.text
    image_data = pending_images.get(user_id)

    if not image_data:
        await update.message.reply_text("⚠️ Image not found. Please start again with /encode.")
        return

    # Hide message using LSB (or simple base64 for now)
    encoded = base64.b64encode(message.encode("utf-8")).decode("utf-8")
    encoded_data[user_id] = encoded

    # Just simulate — in real case, you'd embed the message into the image
    await update.message.reply_text("✅ Your message has been stored with the image.\nNow use /decode and send the same image.")

    # Reset
    user_states.pop(user_id, None)


async def decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_decode_image"
    await update.message.reply_text("📥 Please send the image you want to decode.")


async def get_decode_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_states.get(user_id) != "awaiting_decode_image":
        return

    if not update.message.photo:
        await update.message.reply_text("❗ Please send a valid image.")
        return

    # Simulate decode
    hidden = encoded_data.get(user_id)
    if hidden:
        try:
            decoded = base64.b64decode(hidden.encode("utf-8")).decode("utf-8")
            await update.message.reply_text(f"🕵️ Hidden message:\n\n{decoded}")
        except:
            await update.message.reply_text("⚠️ Failed to decode message.")
    else:
        await update.message.reply_text("🚫 No hidden message found.")

    user_states.pop(user_id, None)


def main():
    """Start the bot."""
    if BOT_TOKEN is None:
        logger.error("No BOT_TOKEN set! Please set the environment variable.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("encode", encode))
    application.add_handler(CommandHandler("decode", decode))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, get_encode_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_hidden_text))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, get_decode_image))

    application.run_polling()


if __name__ == "__main__":
    main()
  
