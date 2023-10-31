import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.exchange import Exchange


class Item:
    def __init__(self, exchange: 'Exchange', base_symbol: str, quote_symbol: str):
        self.exchange = exchange
        self.base_symbol = base_symbol
        self.quote_symbol = quote_symbol

    
    def to_dict(self) -> dict:
        return {
            'exchange': self.exchange.to_dict(),
            'base_symbol': self.base_symbol,
            'quote_symbol': self.quote_symbol
        }

    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())