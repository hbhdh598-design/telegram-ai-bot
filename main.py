import os
import requests
from flask import Flask, request
import telebot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

user_instructions = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 مرحباً بك! أرسل لي أمر التعديل أو أرسل الصورة مباشرة مع وصف التعديل في النص المرفق.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_instructions[message.chat.id] = message.text
    bot.reply_to(message, f"✅ تم حفظ أمر التعديل:\n«{message.text}»\n\nأرسل الصورة الآن ليبدأ التعديل!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    # إما استخدام النص المرفق بالصورة (caption) أو التنسيق المُدخل سابقاً
    prompt = message.caption or user_instructions.get(chat_id, "clean product photo, high quality")
    
    bot.reply_to(message, f"⏳ جاري معالجة الصورة بـ: «{prompt}»... انتظر لحظات.")
    
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
            bot.send_photo(chat_id, response.content, caption="✨ تم تعديل الصورة بنجاح!")
        else:
            bot.reply_to(message, f"⚠️ حدث خطأ من نموذج AI - رمز الاستجابة: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ غير متوقع: {str(e)}")

@app.route(f"/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Bot Webhook is Running Active!", 200

def set_bot_webhook():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{TELEGRAM_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
else:
    set_bot_webhook()
