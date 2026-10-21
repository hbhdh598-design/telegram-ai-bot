import os
import threading
import requests
from flask import Flask
import telebot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_instructions = {}

HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_instructions[message.chat.id] = message.text
    bot.reply_to(message, f"✅ تم حفظ أمر التعديل:\n«{message.text}»\n\nأرسل الصورة الآن ليبدأ التعديل المجاني!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    prompt = user_instructions.get(chat_id, "clean product photo, high quality")
    
    bot.reply_to(message, "⏳ جاري معالجة الصورة عبر الذكاء الاصطناعي... انتظر لحظات.")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        response = requests.post(
            HF_API_URL,
            headers=headers,
            data=downloaded_file,
            params={"parameters": {"prompt": prompt}}
        )
        
        if response.status_code == 200:
            bot.send_photo(chat_id, response.content, caption="✨ تم تعديل الصورة بنجاح (مجاني 100%)!")
        else:
            bot.reply_to(message, f"⚠️ رمز الاستجابة: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running active!"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
