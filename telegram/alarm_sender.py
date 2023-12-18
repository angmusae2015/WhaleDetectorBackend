# 텔레그램 알림 전송

import asyncio
import aioschedule

import sqlite3
from telebot.async_telebot import AsyncTeleBot

from database.database import Database
from database.alarm import Alarm
from database.chat import Chat
from database.channel import Channel


def get_token(file_path):
    with open(file_path, 'r') as file:
        token = file.read().strip()
    return token


token = get_token("../token.txt")
bot = AsyncTeleBot(token)
db = Database("../database/database.db")

tick_alarm_interval = 5
whale_alarm_interval = 30


async def send_tick_alarm():
    enabled_chat_list = db.get_chats(alarm_option=True).values()
    enabled_channel_list = db.get_channels(alarm_option=True).values()
    alarm_list = []
    
    for enabled_chat in enabled_chat_list:
        chat_id = enabled_chat['ChatID']
        chat = Chat(db, chat_id)

        alarm_list += chat.get_alarms(type='TickAlarm', is_enabled=True)

    for enabled_channel in enabled_channel_list:
        channel_id = enabled_channel['ChannelID']
        chat_id = enabled_channel['ChatID']
        chat = Chat(db, chat_id)
        channel = Channel(db, channel_id, chat)

        alarm_list += channel.get_alarms(type='TickAlarm', is_enabled=True)

    for alarm in alarm_list:
        exchange_proxy = alarm.get_item().exchange.get_proxy()

        base_symbol = alarm.get_item().base_symbol
        quote_symbol = alarm.get_item().quote_symbol

        tick_list = exchange_proxy.get_recent_tick_list(base_symbol, quote_symbol, tick_alarm_interval, 500)
        for tick in tick_list:
            if tick.quantity >= alarm.get_quantity():
                chat_id = alarm.chat.id
                await bot.send_message(chat_id, tick.write_tick_msg())


async def send_whale_alarm():
    enabled_chat_list = db.get_chats(alarm_option=True).values()
    enabled_channel_list = db.get_channels(alarm_option=True).values()
    alarm_list = []
    
    for enabled_chat in enabled_chat_list:
        chat_id = enabled_chat['ChatID']
        chat = Chat(db, chat_id)

        alarm_list += chat.get_alarms(type='WhaleAlarm', is_enabled=True)

    for enabled_channel in enabled_channel_list:
        channel_id = enabled_channel['ChannelID']
        chat_id = enabled_channel['ChatID']
        chat = Chat(db, chat_id)
        channel = Channel(db, channel_id, chat)

        alarm_list += channel.get_alarms(type='WhaleAlarm', is_enabled=True)
    
    for alarm in alarm_list:
        exchange_proxy = alarm.get_item().exchange.get_proxy()

        base_symbol = alarm.get_item().base_symbol
        quote_symbol = alarm.get_item().quote_symbol

        orderbook = exchange_proxy.get_orderbook(base_symbol, quote_symbol)
        for whale in orderbook.find_whale(alarm.get_quantity()):
            chat_id = alarm.chat.id
            await bot.send_message(chat_id, whale.write_whale_msg())
    

async def run():
    aioschedule.every(tick_alarm_interval).seconds.do(send_tick_alarm)
    aioschedule.every(whale_alarm_interval).seconds.do(send_whale_alarm)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    task = asyncio.create_task(run())

    await asyncio.gather(task)


asyncio.run(main())