# 텔레그램 명령어 핸들러

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def get_token(file_path):
    with open(file_path, 'r') as file:
        token = file.read().strip()
    return token


token = get_token("token.txt")
bot = TeleBot(token)


@bot.message_handler(commands=['addalarm'])
def start(message):
    chat_id = message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="열기", web_app=WebAppInfo(f"https://whaledetector.kro.kr/add-alarm?chat_id={chat_id}")))

    bot.send_message(chat_id=chat_id, text="알림 추가하기", reply_markup=markup)


bot.infinity_polling()