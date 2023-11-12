# 텔레그램 명령어 핸들러
from typing import TYPE_CHECKING

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from database.database import Database
from telegram import get_bot

if TYPE_CHECKING:
    from telegram import get_bot


bot = get_bot("../token.txt")
database = Database("../database/database.db")
frontend_url = "https://whale-detector-frontend.onrender.com"


@bot.message_handler(commands=['start'])
def register_chat(message):
    chat_id = message.chat.id

    try:
        database.add_chat(chat_id)
    
    except database.ExistingDataError:
        bot.send_message(chat_id=chat_id, text="이미 등록된 채팅입니다.")

    else:
        bot.send_message(chat_id=chat_id, text="환영합니다! /addalarm 명령어로 알림을 추가해보세요.")


@bot.message_handler(commands=['addalarm'])
def add_alarm(message):
    chat_id = message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="열기", web_app=WebAppInfo(f"{frontend_url}/add-alarm?chat={chat_id}")))

    bot.send_message(chat_id=chat_id, text="알림 추가하기", reply_markup=markup)


@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    chat_id = message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="열기", web_app=WebAppInfo(f"{frontend_url}/add-channel?chat={chat_id}")))

    bot.send_message(chat_id=chat_id, text="채널 등록하기", reply_markup=markup)


@bot.message_handler(commands=['editalarm'])
def edit_alarm(message):
    chat_id = message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="열기", web_app=WebAppInfo(f"{frontend_url}/edit-alarm?chat={chat_id}")))

    bot.send_message(chat_id=chat_id, text="알림 On/Off", reply_markup=markup)


if __name__ == "__main__":
    bot.infinity_polling()