# 거래소 API

import requests
from datetime import datetime, timedelta
from typing import Union, List
from database import Database


class Orderbook:
    database = Database("database.db")

    class Unit:
        database = Database("database.db")

        def __init__(self, exchange_id: int, base_symbol: str, quote_symbol: str, check_time: datetime, trade_type: bool, price: float, quantity: float):
            self.exchange_id = exchange_id
            self.base_symbol = base_symbol
            self.qoute_symbol = quote_symbol
            self.check_time = check_time
            self.trade_type = trade_type    # 매도(Ask): True, 매수(Bid): False
            self.price = price
            self.quantity = quantity
            self.total_value = price * quantity

        
        def write_whale_msg(self):
            exchange_name = self.database.get_exchange(self.exchange_id).get_name()
            trade_type_word = "매도" if self.trade_type else "매수"

            msg = f"{exchange_name} {self.base_symbol}/{self.qoute_symbol} 고래 발견!\n\n"
            msg += f"일시: {self.check_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            msg += f"{trade_type_word}벽 {self.base_symbol} {self.quantity:,.3f}@{self.qoute_symbol} {self.price:,.2f}\n"
            msg += f"{self.qoute_symbol} {self.total_value:,.2f}"
            
            return msg


    def __init__(self, exchange_id: int, base_symbol: str, quote_symbol: str, check_time: datetime, ask_unit_info_list: list, bid_unit_info_list: list):
        self.exchange_id = exchange_id
        self.base_symbol = base_symbol
        self.qoute_symbol = quote_symbol
        self.check_time = check_time
        self.ask_units = [
            self.Unit(
                exchange_id, base_symbol, quote_symbol, check_time,
                True, float(unit['Price']), float(unit['Quantity'])
            ) for unit in ask_unit_info_list
        ]
        self.bid_units = [
            self.Unit(
                exchange_id, base_symbol, quote_symbol, check_time,
                True, float(unit['Price']), float(unit['Quantity'])
            ) for unit in bid_unit_info_list
        ]

    
    def find_whale(self, quantity: float) -> List[Unit]:
        ask_whale_list = [unit for unit in self.ask_units if unit.total_value >= quantity]
        bid_whale_list = [unit for unit in self.bid_units if unit.total_value >= quantity]

        return ask_whale_list + bid_whale_list


class Tick:
    database = Database("database.db")

    def __init__(self, exchange_id: int, base_symbol: str, quote_symbol: str, trade_time: datetime, trade_type: bool, price: float, quantity: float):
        self.exchange_id = exchange_id
        self.base_symbol = base_symbol
        self.qoute_symbol = quote_symbol
        self.trade_time = trade_time
        self.trade_type = trade_type    # 매도(Ask): True, 매수(Bid): False
        self.price = price
        self.quantity = quantity

    
    def write_tick_msg(self):
        exchange_name = self.database.get_exchange(self.exchange_id).get_name()
        msg = f"{exchange_name} {self.base_symbol}/{self.qoute_symbol} 체결 발생!\n\n"
        msg += f"일시: {self.trade_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        msg += f"체결량: {self.base_symbol} {self.quantity:,.3f}@{self.qoute_symbol} {self.price:,.2f}\n"
        msg += f"총 거래량: {self.quantity * self.price:,.2f} {self.qoute_symbol}"

        return msg


class ExchangeProxy:
    domain = ""
    item_info_endpoint = ""
    database = Database("database.db")

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

    
    # 화폐 리스트 반환 함수
    # 파라미터가 없을 시 전체 화폐 리스트 반환
    def get_currency(self, currency_symbol=None, english_name=None, korean_name=None):
        url = f"{self.domain}{self.item_info_endpoint}"

        currency_list = []
        for item_info_json in self.__item_iter__(requests.get(url).json()):
            parsed_currency_symbol, parsed_english_name, parsed_korean_name = self.__currency_info_parser__(item_info_json)

            if ((currency_symbol == None or parsed_currency_symbol == currency_symbol)     # 'symbol' 파라미터 존재 또는 미지정 시
                and (english_name == None or parsed_english_name == english_name)    # 'english_name' 파라미터 존재 또는 미지정 시
                and (korean_name == None or parsed_korean_name == korean_name)       # 'korean_name' 파라미터 존재 또는 미지정 시 해당하는 화폐만 리스트에 추가
            ) and len([currency_info for currency_info in currency_list if currency_info['CurrencySymbol'] == parsed_currency_symbol]) == 0:   # 해당 'currencySymbol'을 가진 화폐가 리스트에 없으면 추가
                parsed_currency_info = {
                    'CurrencySymbol': parsed_currency_symbol,
                    'EnglishName': parsed_english_name,
                    'KoreanName': parsed_korean_name
                }

                """ if self.database.is_exists('Currency', parsed_currency_symbol): # 캐싱된 화폐 정보가 있을 경우
                    # 누락된 화폐 정보 추가
                    cached_currency = self.database.get_currency(parsed_currency_symbol)
                    if cached_currency.get_english_name() != None and parsed_currency_info['englishName'] == None:
                        parsed_currency_info['englishName'] = cached_currency.get_english_name()
                    
                    if cached_currency.get_korean_name() != None and parsed_currency_info['koreanName'] == None:
                        parsed_currency_info['koreanName'] = cached_currency.get_korean_name()

                # 캐싱된 화폐 정보가 없고 화폐에 대한 정보가 주어졌을 시
                elif parsed_currency_info['englishName'] is not None or parsed_currency_info['koreanName'] is not None:
                    # 데이터베이스에 정보를 캐싱할 화폐 추가
                    self.database.add_currency(currency_symbol)
                    
                    # 데이터베이스에 화폐 정보 캐싱
                    if parsed_currency_info['englishName'] is not None:
                        self.database.update_currency(currency_symbol, english_name=parsed_currency_info['englishName'])
                    
                    if parsed_currency_info['koreanName'] is not None:
                        self.database.update_currency(currency_symbol, korean_name=parsed_currency_info['koreanName']) """
            
                currency_list.append(parsed_currency_info)

        return currency_list


    # 종목 리스트 반환 함수
    # 파라미터가 없을 시 전체 종목 리스트 반환
    def get_item(self, base_symbol=None, quote_symbol=None):
        url = f"{self.domain}{self.item_info_endpoint}"

        item_list = []
        for item_info_json in self.__item_iter__(requests.get(url).json()):
            parsed_base_symbol, parsed_quote_symbol = self.__item_info_parser__(item_info_json)
            item_info = {
                'BaseSymbol': parsed_base_symbol,
                'QuoteSymbol': parsed_quote_symbol
            }

            if self.database.is_exists('Currency', parsed_base_symbol):
                currency_cache = self.database.get_currency(base_unit)

                item_info['Name'] = currency_cache.get_korean_name() or currency_cache.get_english_name()

            item_list.append(item_info)
        
        # 'base_unit' 또는 'quote_unit' 파라미터 존재 시 해당 파라미터에 부합하는 종목 정보만 반환
        # 파라미터가 주어지지 않았을 시 모든 종목 정보를 반환
        return [
            item for item in item_list
            if (base_symbol is None or item['BaseSymbol'] == base_symbol) and (quote_symbol is None or item['QuoteSymbol'] == quote_symbol)
        ]


class Upbit(ExchangeProxy):
    def __init__(self):
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
        tick_list = [
            Tick(
                1, base_symbol, qoute_symbol,
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

    
    def get_orderbook(self, base_symbol: str, qoute_symbol: str):
        url = f"{self.domain}{self.orderbook_info_endpoint}?markets={qoute_symbol}-{base_symbol}"
        headers = {"accept": "application/json"}

        orderbook_info = requests.get(url, headers=headers).json()[0]

        orderbook = Orderbook(
            1, base_symbol, qoute_symbol,
            datetime.fromtimestamp(int(orderbook_info['timestamp']) / 1000),
            [{"Price": unit['ask_price'], "Quantity": unit['ask_size']} for unit in orderbook_info['orderbook_units']],
            [{"Price": unit['bid_price'], "Quantity": unit['bid_size']} for unit in orderbook_info['orderbook_units']]
        )

        return orderbook


class Binance(ExchangeProxy):
    def __init__(self):
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

        # 이미 조회했던 체결 계약은 제외
        # 마지막으로 조회했던 시점 이후부터의 체결 계약만 리스트에 추가
        tick_list = [
            Tick(
                2, base_symbol, qoute_symbol, datetime.fromtimestamp(int(tick['time']) / 1000),
                bool(tick['isBuyerMaker']),
                float(tick['price']),
                float(tick['qty'])
            ) for tick in requests.get(url, headers=headers).json()
            if datetime.fromtimestamp(int(tick['time']) / 1000) > datetime.now().replace(microsecond=0) + timedelta(seconds=-interval)
        ]

        return tick_list


    def get_orderbook(self, base_symbol: str, quote_symbol: str):
        url = f"{self.domain}{self.orderbook_info_endpoint}?symbol={base_symbol}{quote_symbol}"
        headers = {"accept": "application/json"}

        request_time = datetime.now()
        orderbook_info = requests.get(url, headers=headers).json()

        orderbook = Orderbook(
            2, base_symbol, quote_symbol,
            request_time,
            [{"Price": unit[0], "Quantity": unit[1]} for unit in orderbook_info['asks']],
            [{"Price": unit[0], "Quantity": unit[1]} for unit in orderbook_info['bids']]
        )

        return orderbook