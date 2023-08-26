# 데이터베이스 API

import sqlite3
import os
from typing import Union, List


class DatabaseFileNotFoundError(Exception):
    def __init__(self):
        super().__init__('Could not find database file.')


class ValueNotFoundInDatabaseError(Exception):
    def __init__(self):
        super().__init__('Could not find value with given primary key in database.')


class InvalidPrimaryKeyError(Exception):
    def __init__(self):
        super().__init__('Invalid primary key value or type.')


class DatabaseObject:
    def __init__(self, db: 'Database', primary_key):
        self.db = db
        self.id = primary_key
        self.table_name = self.__class__.__name__

        if not self.is_exists():
            raise ValueNotFoundInDatabaseError

    
    def is_exists(self) -> bool:
        return self.db.is_exists(self.table_name, self.id)

    
    def to_dict(self):
        return self.db.get_by_primary_key(self.table_name, self.id)


class Exchange(DatabaseObject):
    def __init__(self, db: 'Database', exchange_id: int):
        try:
            exchange_id = int(exchange_id)
        
        except:
            raise InvalidPrimaryKeyError
        
        else:
            super().__init__(db, exchange_id)

    
    def get_name(self) -> str:
        return self.to_dict()['ExchangeName']
    

    def get_endpoint(self) -> str:
        return self.to_dict()['ExchangeEndpoint']


class Currency(DatabaseObject):
    def __init__(self, db: 'Database', currency_symbol: str):
        super().__init__(db, str(currency_symbol))
        self.symbol = currency_symbol

    
    def get_english_name(self) -> str:
        return self.to_dict()['EnglishName']
    

    def get_korean_name(self) -> str:
        return self.to_dict()['KoreanName']


class Chat(DatabaseObject):
    def __init__(self, db: 'Database', chat_id: int):
        try:
            chat_id = int(chat_id)
        
        except:
            raise InvalidPrimaryKeyError
        
        else:
            super().__init__(db, chat_id)


    def get_alarm_option(self) -> bool:
        return self.to_dict()['AlarmOption']

    
    def get_channels(self, **kwargs) -> List['Channel']:
        return self.db.get_channel(ChatID=self.id, **kwargs)


    def get_alarms(self, **kwargs) -> List['Alarm']:
        return self.db.get_alarm(ChatID=self.id, **kwargs)
    

class Channel(Chat):
    def __init__(self, db: 'Database', channel_id: int):
        try:
            channel_id = int(channel_id)
        
        except:
            raise InvalidPrimaryKeyError
        
        else:
            super().__init__(db, channel_id)


    def get_name(self) -> str:
        return self.to_dict()['ChannelName']

    
    def get_chat(self) -> Chat:
        return self.db.get_chat(chat_id=self.to_dict()['ChatID'])

    
    def get_channels(self):
        pass


class Alarm(DatabaseObject):
    def __init__(self, db: 'Database', alarm_id: int):
        try:
            alarm_id = int(alarm_id)
        
        except:
            raise InvalidPrimaryKeyError
        
        else:
            super().__init__(db, alarm_id)


    # WhaleAlarm -> 고래 알림
    # TickAlarm -> 체결량 알림
    def get_type(self) -> str:
        return self.to_dict()['AlarmType']

    
    def get_chat(self) -> Union[Chat, Channel]:
        if self.is_channel():
            return self.db.get_channel(self.to_dict()['ChatID'])

        else:
            return self.db.get_chat(self.to_dict()['ChatID'])

    
    def get_exchange(self) -> Exchange:
        return self.db.get_exchange(self.to_dict()['ExchangeID'])


    def get_base_symbol(self) -> str:
        return self.to_dict()['BaseSymbol']

    
    def get_quote_symbol(self) -> str:
        return self.to_dict()['QuoteSymbol']

    
    def get_quantity(self) -> float:
        return self.to_dict()['AlarmQuantity']

    
    def is_enabled(self) -> bool:
        return self.to_dict()['IsEnabled']

    
    def is_channel(self) -> bool:
        return self.to_dict()['IsChannel']


class ResultSet(dict):
    def __init__(self, column: list, result_set: List[list]):
        for row in result_set:
            self.__setitem__(row[0], {key: val for key, val in zip(column, row)})

        self.column = column
        self.result_set = result_set
    
    def to_list(self):
        return self.result_set


class Database:
    class ExistingChatError(Exception):
        def __init__(self):
            super().__init__('This chat is already registered.')


    def __init__(self, db_path="", debug=False, test=False):
        self.db_path = db_path
        self.debug = debug
        self.test = test

        if not self.test and os.path.exists(self.db_path):
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
        
        elif not self.test:
            raise DatabaseFileNotFoundError

    
    # SQL 쿼리문을 작성할 때 코드의 변수를 조건문의 비교 값으로 사용하기 위해
    #   1) 변수가 문자열이라면 따옴표로 감쌈
    #   2) 변수가 부울형이라면 정수형으로 변환
    @staticmethod
    def to_comparison_value(value):
        if type(value) == str:
            return f'\'{value}\''

        elif type(value) == bool:
            return str(int(value))
        
        elif value == None:
            return None
        
        else:
            return str(value)

    
    # 매개변수의 키와 값으로 SQL 쿼리문에 작성할 조건문을 작성
    @staticmethod
    def to_parameter_statement(seperator=" AND ", *args, **kwargs):
        parameter_list = []

        if args == ():    # 키워드 인수로 비교 값이 전달될 경우
            for key, value in kwargs.items():
                parameter_list.append(f"{key}={Database.to_comparison_value(value)}")
        
        elif kwargs == {}:    # 위치 인수로 비교 값이 전달될 경우
            parameter_list = [Database.to_comparison_value(value) for value in args]
            
        return seperator.join(parameter_list)

    
    # 쿼리문을 실행
    def execute(self, query: str) -> ResultSet:
        if self.debug:
            print("================")
            print(f"Query: {query}")

        if not self.test:
            self.cursor.execute(query)
            self.conn.commit()

            try:
                column = [tu[0] for tu in self.cursor.description]
                result_set = self.cursor.fetchall()

                if self.debug:
                    print(f"Result: {result_set}")
            except TypeError:
                return ResultSet([], [])
            else:
                return ResultSet(column, result_set)    # 결과 집합 반환

    
    # 해당 테이블의 컬럼명 반환
    def get_columns(self, table_name: str) -> list:
        result_set = self.execute(f"PRAGMA table_info({table_name});")

        return [row[1] for row in result_set.to_list()]
        
    
    # SELECT문 실행
    def select(self, table_name: str, **kwargs) -> ResultSet:
        query = f"SELECT * FROM {table_name}"
    
        # 조건 지정
        if kwargs != {}:
            query += " WHERE " + self.to_parameter_statement(**kwargs)

        result_set = self.execute(query)

        return result_set   # 결과 집합 반환

    
    # INSERT문 실행
    def insert(self, table_name: str, **kwargs):
        columns = tuple(kwargs.keys())
        values = tuple(kwargs.values())

        query = f"INSERT INTO {table_name} ({self.to_parameter_statement(', ', *columns)}) VALUES ({self.to_parameter_statement(', ', *values)});"
        
        self.execute(query)
        # id = self.execute("SELECT last_insert_rowid();")[0][0]   # 삽입한 열의 ID
        
        # return id
    
    
    # UPDATE문 실행
    def update(self, table_name: str, primary_key, **kwargs):
        primary_key_column = self.get_columns(table_name)[0]
        query = f"UPDATE {table_name} SET {self.to_parameter_statement(', ', **kwargs)} WHERE {primary_key_column}={self.to_comparison_value(primary_key)}"

        self.execute(query)

    
    # DELETE문 실행
    def delete(self, table_name: str, **kwargs):
        query = f"DELETE FROM {table_name}"

        # 조건 지정
        if kwargs != None:
            query += " WHERE " + self.to_parameter_statement(**kwargs)

        self.execute(query)

    
    # 기본 키로 찾기
    def get_by_primary_key(self, table_name: str, primary_key):
        return self.select(table_name)[primary_key]

    
    # 해당 열이 해당 테이블에 존재하는지 확인
    def is_exists(self, table_name: str, primary_key=None, **kwargs) -> bool:
        if primary_key != None:
            primary_key_column = self.get_columns(table_name)[0]
            condition_state = f"{primary_key_column}={self.to_comparison_value(primary_key)}"

        else:
            condition_state = self.parameter_statement(**kwargs)
        
        query = f"SELECT EXISTS(SELECT * FROM {table_name} WHERE {condition_state});"
        result_set = self.execute(query)

        return bool(result_set.to_list()[0][0])


    # 해당 채팅 ID의 채팅이 채널인지 확인
    def is_channel(self, chat_id: int) -> bool:
        if self.is_exists('Chat', chat_id):
            return False
        
        elif self.is_exists('Channel', chat_id):
            return True


    def get_object(self, obj_type, primary_key=None, **kwargs):
        if primary_key != None:
            return obj_type(self, primary_key)
        
        else:
            obj_dict = self.select(obj_type.__name__, **{key: value for key, value in kwargs.items() if value != None})
            return [obj_type(self, key) for key in obj_dict.keys()]


    def get_exchange(self, exchange_id=None, name=None, endpoint=None) -> Union[Exchange, List[Exchange]]:
        return self.get_object(Exchange, primary_key=exchange_id, ExchangeName=name, ExchangeEndpoint=endpoint)

    
    def get_currency(self, currency_symbol=None) -> Union[Currency, List[Currency]]:
        return self.get_object(Currency, primary_key=currency_symbol)

        
    def get_chat(self, chat_id=None, alarm_option=None) -> Union[Chat, List[Chat]]:
        return self.get_object(Chat, primary_key=chat_id, AlarmOption=alarm_option)

    
    def get_channel(self, channel_id=None, name=None, chat_id=None, alarm_option=None) -> Union[Channel, List[Channel]]:
        return self.get_object(Channel, primary_key=channel_id, ChannelName=name, ChatID=chat_id, AlarmOption=alarm_option)

    
    def get_alarm(self, alarm_id=None, type=None, chat_id=None, exchange_id=None, base_symbol=None, quote_symbol=None, quantity=None, is_enabled=None, is_channel=None) -> Union[Alarm, List[Alarm]]:
        return self.get_object(Alarm, primary_key=alarm_id, 
            AlarmType=type,
            ChatID=chat_id,
            ExchangeID=exchange_id,
            BaseSymbol=base_symbol,
            QuoteSymbol=quote_symbol,
            AlarmQuantity=quantity,
            IsEnabled=is_enabled,
            IsChannel=is_channel
        )

    
    def add_chat(self, chat_id, alarm_option=True) -> Chat:
        if not self.is_exists('Chat', chat_id):
            self.insert('Chat', ChatID=chat_id)
            
            return self.get_chat(chat_id=chat_id)
        
        else:
            raise self.ExistingChatError

    
    def add_channel(self, channel_id, name, chat_id, alarm_option=True) -> Channel:
        if not self.is_exists('Channel', channel_id):
            self.insert('Channel', ChannelID=channel_id, ChannelName=name, ChatID=chat_id, AlarmOption=alarm_option)

            return self.get_channel(channel_id=channel_id)
        
        else:
            raise self.ExistingChatError

    
    def add_currency(self, currency_symbol: str):
        self.insert('Currency', CurrencySymbol=currency_symbol)


    def add_alarm(self, type, chat_id, exchange_id, base_symbol, quote_symbol, quantity, is_channel):
        self.insert('Alarm',
            AlarmType=type,
            ChatID=chat_id,
            ExchangeID=exchange_id,
            BaseSymbol=base_symbol,
            QuoteSymbol=quote_symbol,
            AlarmQuantity=quantity,
            IsEnabled=True,
            IsChannel=is_channel
        )

    
    def update_currency(self, currency_symbol: str, english_name=None, korean_name=None):
        if english_name != None:
            self.update('Currency', currency_symbol, EnglishName=english_name)
        
        if korean_name != None:
            self.update('Currency', currency_symbol, KoreanName=korean_name)