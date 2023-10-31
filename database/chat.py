from typing import List, TYPE_CHECKING

from database.database_object import DatabaseObject
from database.database import Database
from database.channel import Channel
from database.alarm import Alarm


class Chat(DatabaseObject):
    def __init__(self, db: Database, chat_id: int):
        super().__init__(db, chat_id)


    def get_alarm_option(self) -> bool:
        return self.get_result_set()['AlarmOption']

    
    def get_channel(self, channel_id: int) -> Channel:
        return Channel(self.db, channel_id, self)

    
    def get_channels(self, **kwargs) -> List[Channel]:
        result_set = self.db.get_channels(chat_id=self.id, **kwargs)
        channel_list = [Channel(self.db, channel_id, self) for channel_id in result_set.keys()]

        return channel_list


    def get_alarm(self, alarm_id: int) -> Alarm:
        return Alarm(self.db, alarm_id, self)


    def get_alarms(self, **kwargs) -> List[Alarm]:
        result_set = self.db.get_alarms(chat_id=self.id, **kwargs)
        alarm_list = [Alarm(self.db, alarm_id, self) for alarm_id in result_set.keys()]

        return alarm_list


    def add_channel(self, channel_id: int, name: str, alarm_option=True) -> Channel:
        added_channel_id = self.db.add_channel(
            channel_id=channel_id,
            name=name,
            chat_id=self.id,
            alarm_option=alarm_option
        )

        added_channel = Channel(self.db, added_channel_id, self)

        return added_channel

    
    def add_alarm(self, type: str, exchange_id: int, base_symbol: str, quote_symbol: str, quantity: float) -> Alarm:
        added_alarm_id = self.db.add_alarm(
            type=type,
            chat_id=self.id,
            exchange_id=exchange_id,
            base_symbol=base_symbol,
            quote_symbol=quote_symbol,
            quantity=quantity,
            is_channel=False
        )

        added_alarm = Alarm(self.db, added_alarm_id, self)

        return added_alarm

    
    def update_alarm_option(self, alarm_option: bool):
        self.db.update(table_name='Chat', primary_key=self.id, AlarmOption=alarm_option)

    
    def delete_channel(self, channel_id: int):
        if channel_id in [channel.id for channel in self.get_channels()]:
            self.db.delete_channel(channel_id)

    
    def delete_alarm(self, alarm_id: int):
        if alarm_id in [alarm.id for alarm in self.get_alarms()]:
            self.db.delete_alarm(alarm_id)

    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'alarm_option': self.get_alarm_option()
        }