# 플라스크 백엔드 서버
import json

from telebot.apihelper import ApiTelegramException
from flask import Flask, request
from flask_cors import CORS

from database.database import Database
from database.chat import Chat
from database.channel import Channel
from database.exchange import Exchange
from database.alarm import Alarm
from server import validate
from telegram.telegram import get_bot


app = Flask(__name__)
CORS(app)
database = Database("../database/database.db")
validator = validate.Validator(database)


# 채팅 정보 요청
@app.get('/chats/<int:chat_id>')
@validator.validate
def get_chat(chat_id: int):
    chat = Chat(database, chat_id)

    return chat.to_json()


# 채팅에 등록된 채널 목록 요청
@app.get('/chats/<int:chat_id>/channels')
@validator.validate
def get_channels_of_chat(chat_id: int):
    chat = Chat(database, chat_id)

    channel_list = chat.get_channels()
    channel_dict_list = [
        channel.to_dict() for channel in channel_list
    ]

    return json.dumps({
        'channels': channel_dict_list
    })


# 채팅의 알림 목록 요청
@app.get('/chats/<int:chat_id>/alarms')
@validator.validate
def get_alarms_of_chat(chat_id: int):
    chat = Chat(database, chat_id)

    alarm_list = chat.get_alarms()
    alarm_dict_list = [
        alarm.to_dict() for alarm in alarm_list
    ]

    return json.dumps({
        'alarms': alarm_dict_list
    })


# 채팅에 알림 등록
@app.post('/chats/<int:chat_id>/alarms')
@validator.validate
def post_alarm_to_chat(chat_id: int):
    chat = Chat(database, chat_id)

    params = json.loads(request.get_data())

    if not params['type'] in ['WhaleAlarm', 'TickAlarm']:
        return "잘못된 알림 유형", 400

    added_alarm = None
    try:
        added_alarm = chat.add_alarm(
            type=params['type'],
            exchange_id=params['exchange_id'],
            base_symbol=params['base_symbol'],
            quote_symbol=params['quote_symbol'],
            quantity=params['quantity']
        )
    
    except Exception as e:
        return "잘못된 매개변수", 400
    
    return added_alarm.to_json()


# 채팅의 알림 정보 요청
@app.get('/chats/<int:chat_id>/alarms/<int:alarm_id>')
@validator.validate
def get_alarm_of_chat_by_id(chat_id: int, alarm_id: int):
    chat = Chat(database, chat_id)
    alarm = chat.get_alarm(alarm_id)

    return alarm.to_json()


# 채팅의 알림 정보 수정
@app.patch('/chats/<int:chat_id>/alarms/<int:alarm_id>')
@validator.validate
def patch_alarm_info_of_chat(chat_id: int, alarm_id: int):
    chat = Chat(database, chat_id)
    alarm = chat.get_alarm(alarm_id)

    params = request.json
    if 'quantity' in params.keys():
        alarm.update_quantity(params['quantity'])
    
    if 'is_enabled' in params.keys():
        alarm.update_enabled(params['is_enabled'])

    return alarm.to_json()


# 채팅의 알림 삭제
@app.delete('/chats/<int:chat_id>/alarms/<int:alarm_id>')
@validator.validate
def delete_alarm_from_chat(chat_id: int, alarm_id: int):
    chat.delete_alarm(alarm_id)

    return "Success", 400


# 채팅에 채널 등록
@app.post('/chats/<int:chat_id>/channels')
@validator.validate
def post_channel_to_chat(chat_id: int):
    chat = Chat(database, chat_id)

    params = json.loads(request.get_data())
    added_channel = None
    try:
        added_channel = chat.add_channel(
            channel_id=params['channel_id'],
            name=params['name']
        )

    except Exception as e:
        return "잘못된 매개변수", 400

    return added_channel.to_json()


# 채팅에 등록된 채널 정보 요청
@app.get('/chats/<int:chat_id>/channels/<channel_id>')
@validator.validate
def get_channel_of_chat_by_id(chat_id: int, channel_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)

    return channel.to_json()


# 채팅에 등록된 채널 정보 수정
@app.patch('/chats/<int:chat_id>/channels/<channel_id>')
@validator.validate
def patch_channel_info(chat_id: int, channel_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)

    params = request.json
    if 'name' in params.keys():
        channel.update_name(params['name'])
    
    if 'alarm_option' in params.keys():
        channel.update_alarm_option(params['alarm_option'])

    return channel.to_json()


# 채팅에서 채널 삭제
@app.delete('/chats/<int:chat_id>/channels/<channel_id>')
@validator.validate
def delete_channel_from_chat(chat_id: int, channel_id: int):
    chat = Chat(database, chat_id)

    chat.delete_channel(channel_id)

    return "Success", 200


# 채팅에 등록된 채널의 알림 목록 요청
@app.get('/chats/<int:chat_id>/channels/<channel_id>/alarms')
@validator.validate
def get_alarms_of_channel(chat_id: int, channel_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)

    alarm_list = channel.get_alarms()
    alarm_dict_list = [
        alarm.to_dict() for alarm in alarm_list
    ]

    return json.dumps({
        'alarms': alarm_dict_list
    })


# 채팅에 등록된 채널에 알림 등록
@app.post('/chats/<int:chat_id>/channels/<channel_id>/alarms')
@validator.validate
def post_alarm_to_channel(chat_id: int, channel_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)

    params = json.loads(request.get_data())
    added_alarm = None
    try:
        added_alarm = channel.add_alarm(
            type=params['type'],
            exchange_id=params['exchange_id'],
            base_symbol=params['base_symbol'],
            quote_symbol=params['quote_symbol'],
            quantity=params['quantity']
        )
    
    except Exception as e:
        return "잘못된 매개변수", 400

    return added_alarm.to_json()


# 채팅에 등록된 채널의 알림 정보 요청
@app.get('/chats/<int:chat_id>/channels/<channel_id>/alarms/<int:alarm_id>')
@validator.validate
def get_alarm_of_channel_by_id(chat_id: int, channel_id: str, alarm_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)
    alarm = channel.get_alarm(alarm_id)

    return alarm.to_json()


# 채팅에 등록된 채널의 알림 정보 수정
@app.patch('/chats/<int:chat_id>/channels/<channel_id>/alarms/<int:alarm_id>')
@validator.validate
def patch_alarm_info_of_channel(chat_id: int, channel_id: str, alarm_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)
    alarm = channel.get_alarm(alarm_id)

    params = request.json
    if 'quantity' in params.keys():
        alarm.update_quantity(params['quantity'])
    
    if 'is_enabled' in params.keys():
        alarm.update_enabled(params['is_enabled'])

    return alarm.to_json()


# 채팅에 등록된 채널의 알림 삭제
@app.delete('/chats/<int:chat_id>/channels/<channel_id>/alarms/<int:alarm_id>')
@validator.validate
def delete_alarm_from_channel(chat_id: int, channel_id: str, alarm_id: int):
    chat = Chat(database, chat_id)
    channel = chat.get_channel(channel_id)

    channel.delete_alarm(alarm_id)

    return "Success", 200


# 거래소 목록 요청
@app.get('/exchanges')
def get_exchanges():
    result_set = database.get_exchanges()
    exchange_list = [Exchange(database, exchange_id) for exchange_id in result_set.keys()]
    exchange_dict_list = [exchange.to_dict() for exchange in exchange_list]

    return json.dumps({
        'exchanges': exchange_dict_list
    })


# 거래소 정보 요청
@app.get('/exchanges/<int:exchange_id>')
def get_exchange_info(exchange_id: int):
    if not database.is_exchange_exists(exchange_id):
        return "존재하지 않는 거래소", 400

    exchange = Exchange(database, exchange_id)

    return exchange.to_json()


# 거래소의 화폐 목록 요청
@app.get('/exchanges/<int:exchange_id>/currencies')
def get_currencies(exchange_id: int):
    if not database.is_exchange_exists(exchange_id):
        return "존재하지 않는 거래소", 400

    exchange = Exchange(database, exchange_id)
    exchange_proxy = exchange.get_proxy()

    currency_dict_list = exchange_proxy.get_currencies()

    response = json.dumps({
        'currencies': currency_dict_list
    })

    return response


# 거래소의 종목 목록 요청
@app.get('/exchanges/<int:exchange_id>/items')
def get_items(exchange_id: int):
    if not database.is_exchange_exists(exchange_id):
        return "존재하지 않는 거래소", 400

    args = request.args
    if not 'base_symbol' in args.keys():
        return "잘못된 매개변수: 'base_symbol' 누락", 401
    
    base_symbol = args['base_symbol']

    exchange = Exchange(database, exchange_id)
    exchange_proxy = exchange.get_proxy()

    item_list = exchange_proxy.get_items(base_symbol=base_symbol)
    item_dict_list = [item.to_dict() for item in item_list]

    response = json.dumps({
        'items': item_dict_list
    })
    
    return response


@app.get('/telegram/get-channel-id')
def get_channel_id():
    bot = get_bot("../token.txt")

    channel_link = ""
    # 채널 링크 파싱
    try:
        channel_link = request.args['channel_link']

    except KeyError:
        return "잘못된 매개변수", 400

    else:
        pass
    
    sended_message = None
    # 채널로 테스트 메시지 전송
    try:
        sended_message = bot.send_message('@' + channel_link, "채널 ID 확인용 메시지입니다.")

    except ApiTelegramException as e:
        error_code = e.error_code
        error_msg = e.description

        return f'{error_code}: {error_msg}', 400

    else:
        channel_id = sended_message.chat.id

        return json.dumps({'channel_id': channel_id})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)