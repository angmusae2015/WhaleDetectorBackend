# 텔레그램 알림 전송

import asyncio
import aioschedule

import sqlite3
from telebot.async_telebot import AsyncTeleBot

from database import Database
from exchange_proxy import Upbit, Binance


def get_token(file_path):
    with open(file_path, 'r') as file:
        token = file.read().strip()
    return token


token = get_token("token.txt")
bot = AsyncTeleBot(token)
db = Database("database.db")
upbit = Upbit()
binance = Binance()

tick_alarm_interval = 5
whale_alarm_interval = 30


async def send_tick_alarm():
    enabled_alarm_list = db.get_alarm(type="TickAlarm", is_enabled=True)
    
    for enabled_alarm in enabled_alarm_list:
        alarm_exchange_id = enabled_alarm.get_exchange().id
        exchange_proxy = upbit if alarm_exchange_id == 1 else binance

        base_symbol = enabled_alarm.get_base_symbol()
        quote_symbol = enabled_alarm.get_quote_symbol()

        tick_list = exchange_proxy.get_recent_tick_list(base_symbol, quote_symbol, tick_alarm_interval, 500)
        for tick in tick_list:
            if tick.quantity >= enabled_alarm.get_quantity():
                chat_id = enabled_alarm.get_chat().id
                await bot.send_message(chat_id, tick.write_tick_msg())


async def send_whale_alarm():
    enabled_alarm_list = db.get_alarm(type="WhaleAlarm", is_enabled=True)

    for enabled_alarm in enabled_alarm_list:
        alarm_exchange_id = enabled_alarm.get_exchange().id
        exchange_proxy = upbit if alarm_exchange_id == 1 else binance

        base_symbol = enabled_alarm.get_base_symbol()
        quote_symbol = enabled_alarm.get_quote_symbol()

        orderbook = exchange_proxy.get_orderbook(base_symbol, quote_symbol)
        for whale in orderbook.find_whale(enabled_alarm.get_quantity()):
            chat_id = enabled_alarm.get_chat().id
            await bot.send_message(chat_id, whale.write_whale_msg())


async def send_alarm():
    aioschedule.every(tick_alarm_interval).seconds.do(send_tick_alarm)
    aioschedule.every(whale_alarm_interval).seconds.do(send_whale_alarm)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    task = asyncio.create_task(send_alarm())

    await asyncio.gather(task)


asyncio.run(main())