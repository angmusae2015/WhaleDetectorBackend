from datetime import datetime
from typing import List

from exchange_proxy.item import Item


class OrderbookUnit():
    def __init__(self, item: Item, check_time: datetime, is_ask: bool, price: float, quantity: float):
        self.item = item
        self.check_time = check_time
        self.is_ask = is_ask    # Ask: 매도, Bid: 매수
        self.price = price
        self.quantity = quantity
        self.total_value = price * quantity

    
    def write_whale_msg(self):
        exchange_name = self.item.exchange.get_name()
        trade_type_word = "매도" if self.is_ask else "매수"

        msg = f"{exchange_name} {self.item.base_symbol}/{self.item.quote_symbol} 고래 발견!\n\n"
        msg += f"일시: {self.check_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        msg += f"{trade_type_word}벽 {self.item.base_symbol} {self.quantity:,.3f}@{self.item.quote_symbol} {self.price:,.2f}\n"
        msg += f"{self.item.quote_symbol} {self.total_value:,.2f}"
        
        return msg


class Orderbook():
    def __init__(self, item: Item, check_time: datetime, ask_units: List[OrderbookUnit], bid_units: List[OrderbookUnit]):
        self.item = item
        self.check_time = check_time
        self.ask_units = ask_units
        self.bid_units = bid_units

    
    def find_whale(self, quantity: float) -> List[OrderbookUnit]:
        ask_whale_list = [unit for unit in self.ask_units if unit.total_value >= quantity]
        bid_whale_list = [unit for unit in self.bid_units if unit.total_value >= quantity]

        return ask_whale_list + bid_whale_list