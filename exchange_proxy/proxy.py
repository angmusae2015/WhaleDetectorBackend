# 거래소 API

import requests
import json
from datetime import datetime, timedelta
from typing import List
from typing import TYPE_CHECKING

from exchange_proxy.item import Item
from exchange_proxy.orderbook import Orderbook, OrderbookUnit
from exchange_proxy.tick import Tick

if TYPE_CHECKING:
    from database.exchange import Exchange


class Proxy:
    domain = ""
    item_info_endpoint = ""

    def __init__(self, exchange: 'Exchange'):
        self.exchange = exchange
    

    # 종목 정보에 대한 API 응답으로부터 종목 정보로 이루어진 이터레이터를 반환하는 함수
    def __item_iter__(self, response_json):
        return None


    # __item_iter__ 함수에서 반환한 이터레이터에서의 각 요소(각 종목에 대한 정보를 담고 있는 json)로부터 
    # 화폐 정보를 반환하는 정보
    def __currency_info_parser__(self, item_info_json):
        return None, None, None # 화폐, 영문 이름, 한글 이름


    # __item_iter__ 함수에서 반환한 이터레이터에서의 각 요소(각 종목에 대한 정보를 담고 있는 json)로부터 
    # 기초 자산(base asset)과 견적 자산(quote asset) 정보를 반환하는 함수
    def __item_info_parser__(self, item_info_json):
        return None, None # 기초 자산 화폐, 견적 자산 화폐

    
    # 전체 화폐 리스트 반환 함수
    def get_currencies(self):
        url = f"{self.domain}{self.item_info_endpoint}"

        currency_list = []
        for item_info_json in self.__item_iter__(requests.get(url).json()):
            parsed_currency_symbol, parsed_english_name, parsed_korean_name = self.__currency_info_parser__(item_info_json)

            parsed_currency_info = {
                'symbol': parsed_currency_symbol,
                'english_name': parsed_english_name,
                'korean_name': parsed_korean_name
            }
            
            is_symbol_duplicate = any(currency_dict['symbol'] == parsed_currency_symbol for currency_dict in currency_list)
            if is_symbol_duplicate:
                continue
            
            currency_list.append(parsed_currency_info)

        return currency_list


    # 종목 리스트 반환 함수
    # 파라미터가 없을 시 전체 종목 리스트 반환
    def get_items(self, base_symbol=None, quote_symbol=None) -> List[Item]:
        url = f"{self.domain}{self.item_info_endpoint}"

        item_list = []
        for item_info_json in self.__item_iter__(requests.get(url).json()):
            parsed_base_symbol, parsed_quote_symbol = self.__item_info_parser__(item_info_json)
            item = Item(self.exchange, parsed_base_symbol, parsed_quote_symbol)

            item_list.append(item)
        
        # 'base_unit' 또는 'quote_unit' 파라미터 존재 시 해당 파라미터에 부합하는 종목 정보만 반환
        # 파라미터가 주어지지 않았을 시 모든 종목 정보를 반환
        filter_base_symbol = lambda item: (base_symbol is None) or (item.base_symbol == base_symbol)
        filter_quote_symbol = lambda item: (quote_symbol is None) or (item.quote_symbol == quote_symbol)
        
        return [
            item for item in item_list
            if filter_base_symbol(item) and filter_quote_symbol(item)
        ]


class Upbit(Proxy):
    def __init__(self, exchange: 'Exchange'):
        self.exchange = exchange
        self.domain = "https://api.upbit.com"
        self.item_info_endpoint = "/v1/market/all"
        self.tick_info_endpoint = "/v1/trades/ticks"
        self.orderbook_info_endpoint = "/v1/orderbook"

    
    def __item_iter__(self, response_json):
        return response_json
    

    def __currency_info_parser__(self, item_info_json):
        return item_info_json['market'].split('-')[1], item_info_json['english_name'], item_info_json['korean_name']

    
    def __item_info_parser__(self, item_info_json):
        return item_info_json['market'].split('-')[::-1]

    
    def get_recent_tick_list(self, base_symbol: str, qoute_symbol: str, interval: int, count=10) -> List[Tick]:
        url = f"{self.domain}{self.tick_info_endpoint}?market={qoute_symbol}-{base_symbol}&count={count}"
        headers = {"accept": "application/json"}

        strptime_from_response = lambda parsed_trade_date, parsed_trade_time: (
            datetime.strptime(f"{parsed_trade_date} {parsed_trade_time}", '%Y-%m-%d %H:%M:%S')
        )

        item = Item(self.exchange, base_symbol, qoute_symbol)

        tick_list = [
            Tick(
                item,
                strptime_from_response(tick['trade_date_utc'], tick['trade_time_utc']),
                True if tick['ask_bid'] == "ASK" else False,
                float(tick['trade_price']),
                float(tick['trade_volume'])
            ) for tick in requests.get(url, headers=headers).json()
            # 이미 조회했던 체결 계약은 제외
            # 마지막으로 조회했던 시점 이후부터의 체결 계약만 리스트에 추가
            if strptime_from_response(tick['trade_date_utc'], tick['trade_time_utc']) > datetime.now().replace(microsecond=0) + timedelta(seconds=-interval)
        ]

        return tick_list

    
    def get_orderbook(self, base_symbol: str, qoute_symbol: str) -> Orderbook:
        url = f"{self.domain}{self.orderbook_info_endpoint}?markets={qoute_symbol}-{base_symbol}"
        headers = {"accept": "application/json"}

        orderbook_info = requests.get(url, headers=headers).json()[0]
        orderbook_unit_dict_list = orderbook_info['orderbook_units']

        item = Item(self.exchange, base_symbol, qoute_symbol)
        check_time = datetime.fromtimestamp(int(orderbook_info['timestamp']) / 1000)
        ask_units = [
            OrderbookUnit(
                item, check_time, True, unit_dict['ask_price'], unit_dict['ask_size']
            ) for unit_dict in orderbook_unit_dict_list
        ]
        bid_units = [
            OrderbookUnit(
                item, check_time, False, unit_dict['bid_price'], unit_dict['bid_size']
            ) for unit_dict in orderbook_unit_dict_list
        ]

        orderbook = Orderbook(item, check_time, ask_units, bid_units)

        return orderbook


class Binance(Proxy):
    def __init__(self, exchange: 'Exchange'):
        self.exchange = exchange
        self.domain = "https://api.binance.com"
        self.item_info_endpoint = "/api/v3/exchangeInfo"
        self.tick_info_endpoint = "/api/v3/trades"
        self.orderbook_info_endpoint = "/api/v3/depth"

    
    def __item_iter__(self, response_json):
        return response_json['symbols']

    
    def __currency_info_parser__(self, item_info_json):
        symbol = item_info_json['baseAsset']

        return symbol, "", ""


    def __item_info_parser__(self, item_info_json):
        return [item_info_json.get(key) for key in ['baseAsset', 'quoteAsset']]

    
    def get_recent_tick_list(self, base_symbol: str, qoute_symbol: str, interval: int, count=10) -> List[Tick]:
        url = f"{self.domain}{self.tick_info_endpoint}?symbol={base_symbol}{qoute_symbol}&limit={count}"
        headers = {"accept": "application/json"}

        item = Item(self.exchange, base_symbol, qoute_symbol)

        # 이미 조회했던 체결 계약은 제외
        # 마지막으로 조회했던 시점 이후부터의 체결 계약만 리스트에 추가
        tick_list = [
            Tick(
                item, datetime.fromtimestamp(int(tick['time']) / 1000),
                bool(tick['isBuyerMaker']),
                float(tick['price']),
                float(tick['qty'])
            ) for tick in requests.get(url, headers=headers).json()
            if datetime.fromtimestamp(int(tick['time']) / 1000) > datetime.now().replace(microsecond=0) + timedelta(seconds=-interval)
        ]

        return tick_list


    def get_orderbook(self, base_symbol: str, quote_symbol: str) -> Orderbook:
        url = f"{self.domain}{self.orderbook_info_endpoint}?symbol={base_symbol}{quote_symbol}"
        headers = {"accept": "application/json"}

        orderbook_info = requests.get(url, headers=headers).json()
        ask_orderbook_unit_tuple_list = orderbook_info['asks']
        bid_orderbook_unit_tuple_list = orderbook_info['bids']

        item = Item(self.exchange, base_symbol, qoute_symbol)
        check_time = datetime.now()
        ask_units = [
            OrderbookUnit(
                item, check_time, True, unit_tuple[0], unit_tuple[1]
            ) for unit_tuple in ask_orderbook_unit_tuple_list
        ]
        bid_units = [
            OrderbookUnit(
                item, check_time, False, unit_tuple[0], unit_tuple[1]
            ) for unit_tuple in bid_orderbook_unit_tuple_list
        ]

        orderbook = Orderbook(item, check_time, ask_units, bid_units)

        return orderbook