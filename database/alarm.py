from typing import List, Union
from typing import TYPE_CHECKING

from database.database_object import DatabaseObject
from database.database import Database
from database.exchange import Exchange
from exchange_proxy.item import Item

if TYPE_CHECKING:
    from chat import Chat
    from channel import Channel


class Alarm(DatabaseObject):
    def __init__(self, db: Database, alarm_id: int, chat: Union['Chat', 'Channel']):
        super().__init__(db, alarm_id)

        self.chat = chat


    # WhaleAlarm -> 고래 알림
    # TickAlarm -> 체결량 알림
    def get_type(self) -> str:
        return self.get_result_set()['AlarmType']

    
    def get_item(self) -> Item:
        exchange_id = self.get_result_set()['ExchangeID']
        exchange = Exchange(self.db, exchange_id)
        base_symbol = self.get_result_set()['BaseSymbol']
        quote_symbol = self.get_result_set()['QuoteSymbol']

        return Item(exchange, base_symbol, quote_symbol)

    
    def get_quantity(self) -> float:
        return self.get_result_set()['AlarmQuantity']

    
    def is_enabled(self) -> bool:
        return self.get_result_set()['IsEnabled']

    
    def is_channel(self) -> bool:
        return self.get_result_set()['IsChannel']


    def update_quantity(self, quantity: float):
        self.db.update(table_name='Alarm', primary_key=self.id, AlarmQuantity=quantity)


    def update_enabled(self, enable: bool):
        self.db.update(table_name='Alarm', primary_key=self.id, IsEnabled=enable)

    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'chat': self.chat.to_dict(),
            'type': self.get_type(),
            'item': self.get_item().to_dict(),
            'quantity': self.get_quantity(),
            'is_enabled': self.is_enabled(),
            'is_channel': self.is_channel()
        }