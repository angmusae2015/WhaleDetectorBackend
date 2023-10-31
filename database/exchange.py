from typing import List, Union, TYPE_CHECKING

from database.database_object import DatabaseObject
from database.database import Database
from exchange_proxy.proxy import Upbit, Binance


class Exchange(DatabaseObject):
    def __init__(self, db: Database, exchange_id: int):
        super().__init__(db, exchange_id)

    
    def get_name(self) -> str:
        return self.get_result_set()['ExchangeName']

    
    def get_proxy(self) -> Union[Upbit, Binance]:
        if self.id == 1:
            return Upbit(self)
        
        elif self.id == 2:
            return Binance(self)

    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.get_name()
        }
