# 플라스크 백엔드 서버

from flask import Flask, request
from flask_cors import CORS
from database import Database
from exchange_proxy import Upbit, Binance
import json

app = Flask(__name__)
CORS(app)
database = Database("database.db")


database_info_endpoint = '/database'

chat_info_endpoint = '/chatinfo'


@app.route('/database/chatinfo', methods=['GET'])
def get_chat_info():
    if request.args.keys():
        chat_info = [chat.to_dict() for chat in database.get_chat(**(request.args))]

    return json.dumps({'chat_info': chat_info})


@app.route('/database/exchangeinfo', methods=['GET'])
def get_exchange_info():
    exchange_info = [exchange.to_dict() for exchange in database.get_exchange(**(request.args))]

    return json.dumps({'exchange_info': exchange_info})


@app.route('/database/channelinfo', methods=['GET'])
def get_channel_info():
    if request.args.keys():
        channel_info = [channel.to_dict() for channel in database.get_channel(**(request.args))]

    return json.dumps({'channel_info': channel_info})


@app.route('/database/alarm/create', methods=['POST'])
def add_alarm():
    params = json.loads(request.get_data())
    database.add_alarm(**params)

    print("Success!")

    return "Success!"


@app.route('/upbit/itemlist', methods=['GET'])
def get_upbit_item():
    upbit = Upbit()

    # 가능한 파라미터:
    # base_unit, quote_unit
    item_list = upbit.get_item(**(request.args))

    return json.dumps({'item_info': item_list})


@app.route('/upbit/currencylist', methods=['GET'])
def get_upbit_currency():
    upbit = Upbit()

    # 가능한 파라미터:
    # symbol, english_name, korean_name
    currency_list = upbit.get_currency(**(request.args))

    return json.dumps({'currency_info': currency_list})


@app.route('/binance/itemlist', methods=['GET'])
def get_binance_item():
    binance = Binance()

    # 가능한 파라미터:
    # base_unit, quote_unit
    item_list = binance.get_item(**(request.args))

    return json.dumps({'item_info': item_list})


@app.route('/binance/currencylist', methods=['GET'])
def get_binance_currency():
    binance = Binance()

    # 가능한 파라미터:
    # symbol, english_name, korean_name
    currency_list = binance.get_currency(**(request.args))

    return json.dumps({'currency_info': currency_list})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)