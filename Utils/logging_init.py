import logging
from Utils.telebot_init import bot

import os
from dotenv import load_dotenv
load_dotenv()

# Configuring logging to send logs to a telegram group
class TelegramHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        bot.send_message(chat_id=chat_id, text=log_entry, parse_mode='HTML')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%Y %H:%M:%S', handlers=[TelegramHandler()])
telegram_logger = logging.getLogger('telegram_logger')
chat_id = os.getenv('logging_chat_id')