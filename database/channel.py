from typing import List
from typing import TYPE_CHECKING

from database.database import Database
from database.database_object import DatabaseObject
from database.alarm import Alarm

if TYPE_CHECKING:
    from chat import Chat


class Channel(DatabaseObject):
    def __init__(self, db: Database, channel_id: int, chat: 'Chat'):
        super().__init__(db, channel_id)

        self.chat = chat
    

    def get_alarm_option(self) -> bool:
        return self.get_result_set()['AlarmOption']


    def get_name(self) -> str:
        return self.get_result_set()['ChannelName']


    def get_alarm(self, alarm_id: int) -> Alarm:
        return Alarm(self.db, alarm_id, self)

    
    def get_alarms(self, **kwargs) -> List[Alarm]:
        result_set = self.db.get_alarms(chat_id=self.id, is_channel=True, **kwargs)
        alarm_list = [Alarm(self.db, alarm_id, self) for alarm_id in result_set.keys()]

        return alarm_list


    def add_alarm(self, type: str, exchange_id: int, base_symbol: str, quote_symbol:str, quantity: float) -> Alarm:
        added_alarm_id = self.db.add_alarm(
            type=type,
            chat_id=self.id,
            exchange_id=exchange_id,
            base_symbol=base_symbol,
            quote_symbol=quote_symbol,
            quantity=quantity,
            is_channel=True
        )

        added_alarm = Alarm(self.db, added_alarm_id, self)

        return added_alarm

    
    def update_alarm_option(self, alarm_option: bool):
        self.db.update(table_name='Channel', primary_key=self.id, AlarmOption=alarm_option)

    
    def update_name(self, name: str):
        self.db.update(table_name='Channel', primary_key=self.id, ChannelName=name)


    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.get_name(),
            'chat': self.chat.to_dict(),
            'alarm_option': self.get_alarm_option()
        }