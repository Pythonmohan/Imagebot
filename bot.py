import io
import logging
from PIL import Image
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# Function to encode the hidden message into the image
def lsb_encode(image_bytes, message):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    binary_msg = ''.join(format(ord(c), '08b') for c in message) + '1111111111111110'
    pixels = list(image.getdata())
    new_pixels = []

    idx = 0
    for pixel in pixels:
        r, g, b = pixel
        if idx < len(binary_msg):
            r = (r & ~1) | int(binary_msg[idx])
            idx += 1
        if idx < len(binary_msg):
            g = (g & ~1) | int(binary_msg[idx])
            idx += 1
        if idx < len(binary_msg):
            b = (b & ~1) | int(binary_msg[idx])
            idx += 1
        new_pixels.append((r, g, b))

    image.putdata(new_pixels)
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output

# Function to decode the hidden message from the image
def lsb_decode(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    binary = ""
    for pixel in list(image.getdata()):
        for channel in pixel[:3]:
            binary += str(channel & 1)
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    message = ""
    for c in chars:
        if c == '11111110':
            break
        message += chr(int(c, 2))
    return message

# Command to start the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Steganography Bot! Send me an image to encode or decode.")

# Command to encode a message into an image
def encode(update: Update, context: CallbackContext):
    update.message.reply_text("Please send an image to encode your message.")

# Receive image and process it for encoding
def get_encode_image(update: Update, context: CallbackContext):
    if not update.message.photo:
        update.message.reply_text("⚠️ Please send a valid image.")
        return
    image_id = update.message.photo[-1].file_id
    image_file = context.bot.get_file(image_id)
    image_bytes = image_file.download_as_bytearray()

    # Save the image for later use
    context.user_data["encode_image_bytes"] = image_bytes
    update.message.reply_text("Image received! Now send me the message you want to hide.")

# Receive hidden text and encode it into the image
def get_hidden_text(update: Update, context: CallbackContext):
    message = update.message.text
    image_bytes = context.user_data.get("encode_image_bytes")
    if not image_bytes:
        update.message.reply_text("⚠️ No image found. Please start again with /encode.")
        return

    encoded_img = lsb_encode(image_bytes, message)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=encoded_img, caption="✅ Hidden message encoded.")

# Command to decode the hidden message from an image
def decode(update: Update, context: CallbackContext):
    update.message.reply_text("Please send the image to decode its hidden message.")

# Receive image and decode the hidden message
def get_decode_image(update: Update, context: CallbackContext):
    if not update.message.photo:
        update.message.reply_text("⚠️ Please send a valid image.")
        return
    image_id = update.message.photo[-1].file_id
    image_file = context.bot.get_file(image_id)
    image_bytes = image_file.download_as_bytearray()

    hidden_message = lsb_decode(image_bytes)
    if hidden_message:
        update.message.reply_text(f"🔍 Hidden Message: {hidden_message}")
    else:
        update.message.reply_text("❌ No hidden message found.")

def main():
    """Start the bot."""
    updater = Updater(BOT_TOKEN, use_context=True)
    
    # Dispatcher to register handlers
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("encode", encode))
    dp.add_handler(CommandHandler("decode", decode))

    # Message handlers
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, get_encode_image))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, get_hidden_text))
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, get_decode_image))

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl+C is pressed
    updater.idle()

if __name__ == '__main__':
    main()
