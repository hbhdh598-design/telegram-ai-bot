import os
import io
from flask import Flask, request
import telebot
from PIL import Image, ImageDraw, ImageFont

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك يا قائد! أرسل أي صورة وسأقوم بتعديلها وتنظيفها وإضافة النص المطلوب عليها فوراً.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    caption_text = message.caption or "Clean Product"
    
    sent_msg = bot.reply_to(message, "⏳ جارٍ معالجة وتنسيق الصورة...")
    
    try:
        # تحميل الصورة من تيليجرام
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح الصورة باستخدام مكتبة المعالجة
        image = Image.open(io.BytesIO(downloaded_file)).convert("RGB")
        width, height = image.size
        
        # إجراء تعديل احترافي (مثلاً قص الأجزاء السفلية لتنظيف أرقام الهواتف أو الشعارات غير المنسقة)
        # سنقوم بقص الجزء السفلي بنسبة 10% لتنظيف الخلفية والأسفل كما طلبت سابقاً
        crop_height = int(height * 0.90)
        cleaned_image = image.crop((0, 0, width, crop_height))
        
        # حفظ الصورة المعدلة في ذاكرة المؤقتة
        output = io.BytesIO()
        cleaned_image.save(output, format="JPEG", quality=95)
        output.seek(0)
        
        # إرسال الصورة النظيفة للـ قائد
        bot.send_photo(
            chat_id, 
            output, 
            caption=f"✨ تم تنظيف وتنسيق الصورة بنجاح!\n📝 الوصف: {caption_text}"
        )
        bot.delete_message(chat_id, sent_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة: {str(e)}", chat_id, sent_msg.message_id)

@app.route(f"/{TELEGRAM_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Image Processing Bot is Active!", 200

# ربط الـ Webhook تلقائياً
render_url = os.environ.get("RENDER_EXTERNAL_URL")
if render_url:
    bot.remove_webhook()
    bot.set_webhook(url=f"{render_url}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
