import sys
sys.path.append('/home/whaledetectordev2/backend')

from database.database import Database
from database.chat import Chat
from database.channel import Channel
from database.exchange import Exchange
from database.alarm import Alarm


class Validator():
    def __init__(self, database: Database):
        self.database = database


    def validate_chat(self, chat_id: int):
        if not self.database.is_chat_exists(chat_id):
            return False, "존재하지 않는 채팅"

        return True, ""


    def validate_channel(self, chat_id: int, channel_id: int):
        is_chat_valid, error_message = self.validate_chat(chat_id)
        if not is_chat_valid:
            return False, error_message
        
        chat = Chat(self.database, chat_id)
        if not channel_id in [channel.id for channel in chat.get_channels()]:
            return False, "존재하지 않는 채널"

        return True, ""


    def validate_chat_alarm(self, chat_id: int, alarm_id: int):
        is_chat_valid, error_message = self.validate_chat(chat_id)
        if not is_chat_valid:
            return is_chat_valid, error_message
        
        chat = Chat(self.database, chat_id)
        if not alarm_id in [alarm.id for alarm in chat.get_alarms()]:
            return False, "존재하지 않는 알림"
        
        return True, ""

    
    def validate_channel_alarm(self, chat_id: int, channel_id: int, alarm_id: int):
        is_channel_valid, error_message = self.validate_channel(chat_id, channel_id)
        if not is_channel_valid:
            return is_channel_valid, error_message
        
        chat = Chat(self.database, chat_id)
        channel = Channel(self.database, channel_id, chat)
        if not alarm_id in [alarm.id for alarm in channel.get_alarms()]:
            return False, "존재하지 않는 알림"
        
        return True, ""

    
    def validate(self, func):
        def wrapper(*args, **kwargs):
            # 채널 ID는 음수로 문자열로 전달되므로 정수형으로 변환해야 함
            if 'channel_id' in kwargs.keys():
                kwargs['channel_id'] = int(kwargs['channel_id'])

            validation_func = None
            if 'alarm_id' in kwargs.keys():
                if 'channel_id' in kwargs.keys():
                    validation_func = self.validate_channel_alarm
                
                elif 'chat_id' in kwargs.keys():
                    validation_func = self.validate_chat_alarm
            
            elif 'channel_id' in kwargs.keys():
                validation_func = self.validate_channel
            
            elif 'chat_id' in kwargs.keys():
                validation_func = self.validate_chat
            
            is_valid, error_message = validation_func(**kwargs)
            if not is_valid:
                return error_message, 400
            
            return func(*args, **kwargs)
            
        wrapper.__name__ = func.__name__
        
        return wrapper