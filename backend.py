# 플라스크 백엔드 서버
import json

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from flask import Flask, request
from flask_cors import CORS

from database import Database
from exchange import get_exchange


app = Flask(__name__)
CORS(app)

database = None
with open('./token.json', 'r') as file:
    tokens = json.load(file)
    database = Database(tokens['database_url'])


def channel_row_to_dict(row) -> dict:
    return {
        'id': row['channel_id'],
        'name': row['channel_name']
    }


def alarm_row_to_dict(row) -> dict:
    return {
        'id': row['alarm_id'],
        'item': {
            'exchange_id': row['exchange_id'],
            'base_symbol': row['base_symbol'],
            'quote_symbol': row['quote_symbol']
        },
        'condition': row['alarm_condition'],
        'is_enabled': row['is_enabled']
    }


def exchange_row_to_dict(row) -> dict:
    return {
        'id': row['exchange_id'],
        'name': row['exchange_name']
    }


# 채팅 목록 요청
@app.get('/chats')
def get_chats():
    chat_id_list = list(database.select(table_name='chat').keys())

    return json.dumps({
        'chats': chat_id_list
    })

# 채팅 등록
@app.post('/chats/<int:chat_id>')
def post_chat(chat_id: int):
    if database.is_chat_exists(chat_id):
        return "이미 등록된 채팅"
    
    try:
        database.insert(table_name='chat', chat_id=chat_id)

    except Exception as e:
        return f"등록 실패: {e.args[0]}", 400

    return '등록 성공', 200


# 채팅 삭제
@app.delete('/chats/<int:chat_id>')
def delete_chat(chat_id: int):
    if not database.is_chat_exists(chat_id):
        return '등록되지 않은 채팅', 400

    try:
        database.delete(table_name='chat', chat_id=chat_id)
    
    except Exception as e:
        return f"삭제 실패: {e.args[0]}", 400

    return "삭제 성공", 200


# 채널 목록 요청
@app.get('/channels')
def get_channels():
    result_set = database.select(table_name='channel')

    channel_dict_list = [
        channel_row_to_dict(row) for row in result_set.to_list()
    ]

    return json.dumps({
        'channels': channel_dict_list
    })


# 채널 등록
@app.post('/channels')
def post_channel():
    params = json.loads(request.get_data())

    channel_id, channel_name = None, None
    try:
        channel_id = params['channel_id']
        channel_name = params['channel_name']

    except Exception as e:
        return "잘못된 매개 변수", 400

    if database.is_channel_exists(channel_id):
        return '이미 등록된 채널', 400

    try:
        database.insert(table_name='channel', channel_id=channel_id, channel_name=channel_name)
    
    except Exception as e:
        return f"등록 실패: {e.args[0]}", 400

    return '등록 성공', 200


# 채널 삭제
@app.delete('/channels/<int:channel_id>')
def delete_channel(channel_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채팅', 400

    try:
        database.delete(table_name='channel', channel_id=channel_id)

    except Exception as e:
        return f"삭제 실패: {e.args[0]}", 400

    return "삭제 성공", 200


# 채널 정보 요청
@app.get('/channels/<int:channel_id>')
def get_channel_info(channel_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    result_set = database.select(table_name='channel', channel_id=channel_id)
    row = result_set[channel_id]

    return json.dumps(channel_row_to_dict(row))


# 채널의 알림 목록 요청
@app.get('/channels/<int:channel_id>/alarms')
def get_alarms(channel_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    result_set = database.select(table_name='alarm', channel_id=channel_id)

    alarm_dict_list = [
        alarm_row_to_dict(row) for row in result_set.to_list()
    ]

    return json.dumps({
        'alarms': alarm_dict_list
    })


# 채널에 알림 등록
@app.post('/channels/<int:channel_id>/alarms')
def post_alarm(channel_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    params = json.loads(request.get_data())

    added_alarm_id = None
    try:
        added_alarm_id = database.insert(
            table_name='alarm',
            exchange_id=params['exchange_id'],
            base_symbol=params['base_symbol'],
            quote_symbol=params['quote_symbol'],
            alarm_condition=params['condition']
        )
    
    except Exception as e:
        return "잘못된 매개변수", 400

    else:
        added_alarm_row = database.select(table_name='alarm', alarm_id=added_alarm_id)[added_alarm_id]

        return json.dumps(alarm_row_to_dict(added_alarm_row))


# 채널의 알림 정보 요청
@app.get('/channels/<int:channel_id>/alarms/<int:alarm_id>')
def get_alarm_info(channel_id: int, alarm_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    result_set = database.select(table_name='alarm', alarm_id=alarm_id)
    if len(result_set) == 0:
        return '등록되지 않은 알림', 400

    return json.dumps(alarm_row_to_dict(result_set[alarm_id]))


# 채널의 알림 정보 수정
@app.patch('/channels/<int:channel_id>/alarms/<int:alarm_id>')
def patch_alarm_info(channel_id: int, alarm_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    if not database.is_alarm_exists(alarm_id):
        return '등록되지 않은 알림', 400

    params = request.json
    if 'condition' in params.keys():
        database.update(table_name='alarm', primary_key=alarm_id, alarm_condition=params['condition'])
    
    if 'is_enabled' in params.keys():
        database.update(table_name='alarm', primary_key=alarm_id, is_enabled=params['is_enabled'])

    alarm_row = database.select(table_name='alarm', alarm_id=alarm_id)[alarm_id]

    return json.dumps(alarm_row_to_dict(alarm_row))


# 채널에서 알림 삭제
@app.delete('/channels/<int:channel_id>/alarms/<int:alarm_id>')
def delete_alarm(channel_id: int, alarm_id: int):
    if not database.is_channel_exists(channel_id):
        return '등록되지 않은 채널', 400

    if not database.is_alarm_exists(alarm_id):
        return '등록되지 않은 알림', 400

    database.delete(table_name='alarm', alarm_id=alarm_id)

    return "삭제 성공", 200


# 거래소 목록 요청
@app.get('/exchanges')
def get_exchanges():
    result_set = database.select(table_name='exchange')
    exchange_dict_list = [exchange_row_to_dict(row) for row in result_set.to_list()]

    return json.dumps({
        'exchanges': exchange_dict_list
    })


# 거래소 정보 요청
@app.get('/exchanges/<int:exchange_id>')
def get_exchange_info(exchange_id: int):
    if not database.is_exchange_exists(exchange_id):
        return "존재하지 않는 거래소", 400

    result_set = database.select(table_name='exchange', exchange_id=exchange_id)
    exchange_row = result_set[exchange_id]

    return json.dumps(exchange_row_to_dict(exchange_row))


# 거래소의 화폐 목록 요청
@app.get('/exchanges/<int:exchange_id>/currencies')
def get_currencies(exchange_id: int):
    if not database.is_exchange_exists(exchange_id):
        return "존재하지 않는 거래소", 400

    exchange = get_exchange(exchange_id)
    currency_dict_list = exchange.get_currencies()

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
        return "잘못된 매개변수: 'base_symbol' 누락", 400
    
    base_symbol = args['base_symbol']

    exchange = get_exchange(exchange_id)
    item_dict_list = exchange.get_items(base_symbol=base_symbol)

    response = json.dumps({
        'items': item_dict_list
    })
    
    return response


@app.get('/telegram/get-channel-id')
def get_channel_id():
    bot = None
    with open('token.txt', 'r') as file:
        token = file.read().strip()
        bot = TeleBot(token)

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
    app.run(host='0.0.0.0', port=5000)