# 거래소 API

import requests
import json
from typing import List


class Exchange:
    domain = ""
    item_info_endpoint = ""


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
    def get_items(self, base_symbol=None, quote_symbol=None) -> List[dict]:
        url = f"{self.domain}{self.item_info_endpoint}"

        item_list = []
        for item_info_json in self.__item_iter__(requests.get(url).json()):
            parsed_base_symbol, parsed_quote_symbol = self.__item_info_parser__(item_info_json)
            item = {
                'base_symbol': parsed_base_symbol,
                'quote_symbol': parsed_quote_symbol
            }

            item_list.append(item)
        
        # 'base_unit' 또는 'quote_unit' 파라미터 존재 시 해당 파라미터에 부합하는 종목 정보만 반환
        # 파라미터가 주어지지 않았을 시 모든 종목 정보를 반환
        filter_base_symbol = lambda item: (base_symbol is None) or (item['base_symbol'] == base_symbol)
        filter_quote_symbol = lambda item: (quote_symbol is None) or (item['quote_symbol'] == quote_symbol)
        
        return [
            item for item in item_list
            if filter_base_symbol(item) and filter_quote_symbol(item)
        ]


class Upbit(Exchange):
    def __init__(self):
        self.domain = "https://api.upbit.com"
        self.item_info_endpoint = "/v1/market/all"

    
    def __item_iter__(self, response_json):
        return response_json
    

    def __currency_info_parser__(self, item_info_json):
        return item_info_json['market'].split('-')[1], item_info_json['english_name'], item_info_json['korean_name']

    
    def __item_info_parser__(self, item_info_json):
        return item_info_json['market'].split('-')[::-1]


class Binance(Exchange):
    def __init__(self):
        self.domain = "https://api.binance.com"
        self.item_info_endpoint = "/api/v3/exchangeInfo"

    
    def __item_iter__(self, response_json):
        return response_json['symbols']

    
    def __currency_info_parser__(self, item_info_json):
        symbol = item_info_json['baseAsset']

        return symbol, "", ""


    def __item_info_parser__(self, item_info_json):
        return [item_info_json.get(key) for key in ['baseAsset', 'quoteAsset']]


def get_exchange(exchange_id: int):
    if exchange_id == 1:
        return Upbit()
    
    elif exchange_id == 2:
        return Binance()