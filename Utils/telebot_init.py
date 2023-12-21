import telebot

import os
from dotenv import load_dotenv
load_dotenv()

###########################
# Telebot initialization #
###########################
# Create a TeleBot instance
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)