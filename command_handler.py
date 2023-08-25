# 텔레그램 명령어 핸들러

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from database import Database


def get_token(file_path):
    with open(file_path, 'r') as file:
        token = file.read().strip()
    return token


def get_bot(file_path) -> TeleBot:
    token = get_token(file_path)

    return TeleBot(token)


bot = get_bot("token.txt")
database = Database("database.db")


@bot.message_handler(commands=['start'])
def register_chat(message):
    chat_id = message.chat.id

    try:
        database.add_chat(chat_id)
    
    except database.ExistingChatError:
        bot.send_message(chat_id=chat_id, text="이미 등록된 채팅입니다.")

    else:
        bot.send_message(chat_id=chat_id, text="환영합니다! /addalarm 명령어로 알림을 추가해보세요.")


@bot.message_handler(commands=['addalarm'])
def add_alarm(message):
    chat_id = message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="열기", web_app=WebAppInfo(f"https://whaledetector.kro.kr/add-alarm?chat_id={chat_id}")))

    bot.send_message(chat_id=chat_id, text="알림 추가하기", reply_markup=markup)


if __name__ == "__main__":
    bot.infinity_polling()