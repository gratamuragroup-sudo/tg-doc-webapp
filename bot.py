import json
import logging
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from docxtpl import DocxTemplate

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8965670570:AAEJYQvsnxrPRym6bGCIIc4URS7KXUnddwo"
WEB_APP_URL = "https://gratamuragroup-sudo.github.io/tg-doc-webapp/?v=13"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    web_app_button = KeyboardButton(
        text="📝 Заполнить доверенность", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    reply_markup = ReplyKeyboardMarkup([[web_app_button]], resize_keyboard=True)
    
    await update.message.reply_text(
        "Нажмите на кнопку ниже, чтобы открыть форму и сформировать документ:",
        reply_markup=reply_markup
    )

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_data = update.effective_message.web_app_data.data
        logging.info(f"Получены данные из WebApp: {raw_data}")
        data = json.loads(raw_data)
        
        # Показываем пользователю, что бот уже прикрепляет документ
        await update.message.reply_chat_action("upload_document")

        template_path = "template.docx"
        if not os.path.exists(template_path):
            await update.message.reply_text("❌ Ошибка: файл 'template.docx' не найден!")
            return

        # Рендеринг в памяти
        doc = DocxTemplate(template_path)
        doc.render(data)
        
        user_id = update.effective_user.id
        doc_num = str(data.get('number', user_id)).replace('/', '_').replace('\\', '_')
        output_filename = f"Доверенность_{doc_num}.docx"
        doc.save(output_filename)
        
        # Отправка готового файла
        with open(output_filename, 'rb') as document_file:
            await update.message.reply_document(
                document=document_file,
                caption="✅ Ваша доверенность успешно сформирована!"
            )
            
        if os.path.exists(output_filename):
            os.remove(output_filename)
            
    except Exception as e:
        logging.error(f"Ошибка при генерации файла: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Произошла ошибка при генерации документа: {e}")

def main():
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )
    
    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

    print("🚀 Бот успешно запущен и ждет команд...")
    app.run_polling()

if __name__ == "__main__":
    main()
