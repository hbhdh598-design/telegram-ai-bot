import os
import requests
from flask import Flask, request
import telebot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# استخدام نموذج نص إلى صورة / تعديل عام أكثر استقراراً
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 مرحباً بك يا قائد! أرسل لي أي صورة مع وصف التعديل باللغة الإنجليزية في الـ Caption وسأقوم بمعالجتها فوراً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    prompt = message.caption or "High quality product photography, clean background"
    
    sent_msg = bot.reply_to(message, "⏳ جارٍ معالجة الصورة عبر نموذج الذكاء الاصطناعي... قد يستغرق الأمر دقيقة.")
    
    try:
        # تحميل الصورة المرسلة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # إرسال الطلب لنموذج Hugging Face
        response = requests.post(
            HF_API_URL,
            headers=headers,
            data=downloaded_file
        )
        
        if response.status_code == 200:
            bot.send_photo(chat_id, response.content, caption="✨ تم تعديل ومعالجة الصورة بنجاح بواسطة بوت أثير!")
        else:
            bot.edit_message_text(f"⚠️ النموذج محمل حالياً أو يتطلب وقتاً للإقلاع (رمز الخطأ: {response.status_code}). حاول مجدداً بعد قليل.", chat_id, sent_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ تقني: {str(e)}", chat_id, sent_msg.message_id)

@app.route(f"/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Bot Webhook is Active & Ready!", 200

# ربط الـ Webhook تلقائياً عند الإقلاع
render_url = os.environ.get("RENDER_EXTERNAL_URL")
if render_url:
    bot.remove_webhook()
    bot.set_webhook(url=f"{render_url}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
