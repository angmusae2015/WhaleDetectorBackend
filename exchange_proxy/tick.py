from datetime import datetime

from exchange_proxy.item import Item


class Tick:
    def __init__(self, item: Item, trade_time: datetime, is_ask: bool, price: float, quantity: float):
        self.item = item
        self.trade_time = trade_time
        self.is_ask = is_ask   # 매도(Ask): True, 매수(Bid): False
        self.price = price
        self.quantity = quantity

    
    def write_tick_msg(self):
        exchange_name = self.item.exchange.get_name()
        base_symbol = self.item.base_symbol
        quote_symbol = self.item.quote_symbol
        
        msg = f"{exchange_name} {base_symbol}/{quote_symbol} 체결 발생!\n\n"
        msg += f"일시: {self.trade_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        msg += f"체결량: {base_symbol} {self.quantity:,.3f}@{quote_symbol} {self.price:,.2f}\n"
        msg += f"총 거래량: {self.quantity * self.price:,.2f} {quote_symbol}"

        return msg