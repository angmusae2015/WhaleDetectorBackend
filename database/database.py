# 데이터베이스 API
import os
import json
from typing import Union, List

import sqlite3


class DatabaseFileNotFoundError(Exception):
    def __init__(self):
        super().__init__('Could not find database file.')


class ResultSet(dict):
    def __init__(self, column: list, result_set: List[list]):
        for row in result_set:
            self.__setitem__(row[0], {key: val for key, val in zip(column, row)})

        self.column = column
        self.result_set = result_set
    
    def to_list(self):
        return self.result_set


class Database:
    class ExistingDataError(Exception):
        def __init__(self):
            super().__init__('This data already exists.')


    def __init__(self, db_path="", debug=False, test=False):
        self.db_path = db_path
        self.debug = debug
        self.test = test

        if not self.test and os.path.exists(self.db_path):
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
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
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            try:
                cursor.execute(query)
            
            except sqlite3.ProgrammingError as error:
                print("Recursive error while executing: " + query)

            self.conn.commit()

            try:
                column = [tu[0] for tu in cursor.description]
                result_set = cursor.fetchall()

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
        primary_key = self.execute("SELECT last_insert_rowid();").to_list()[0][0]   # 삽입한 열의 ID
        
        return primary_key
    
    
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

    
    def is_exchange_exists(self, exchange_id: int) -> bool:
        return self.is_exists(table_name='Exchange', primary_key=exchange_id)

    
    def is_chat_exists(self, chat_id: int) -> bool:
        return self.is_exists(table_name='Chat', primary_key=chat_id)


    def is_channel_exists(self, channel_id: int) -> bool:
        return self.is_exists(table_name='Channel', primary_key=channel_id)

    
    def is_alarm_exists(self, alarm_id: int) -> bool:
        return self.is_exists(table_name='Alarm', primary_key=alarm_id)


    # 해당 채팅 ID의 채팅이 채널인지 확인
    def is_channel(self, chat_id: int) -> bool:
        if self.is_exists('Chat', chat_id):
            return False
        
        elif self.is_exists('Channel', chat_id):
            return True


    def get_by_primary_key(self, table_name: str, primary_key) -> dict:
        return self.select(table_name)[primary_key]


    def get_objects(self, table_name: str, **kwargs) -> ResultSet:
        result_set = self.select(table_name, **{key: value for key, value in kwargs.items() if value != None})
        return result_set


    def get_exchanges(self, name=None, endpoint=None) -> ResultSet:
        return self.get_objects('Exchange', ExchangeName=name, ExchangeEndpoint=endpoint)

        
    def get_chats(self, alarm_option=None) -> ResultSet:
        return self.get_objects('Chat', AlarmOption=alarm_option)

    
    def get_channels(self, name=None, chat_id=None, alarm_option=None) -> ResultSet:
        return self.get_objects('Channel', ChannelName=name, ChatID=chat_id, AlarmOption=alarm_option)

    
    def get_alarms(self, type=None, chat_id=None, exchange_id=None, base_symbol=None, quote_symbol=None, quantity=None, is_enabled=None, is_channel=None) -> ResultSet:
        return self.get_objects('Alarm', 
            AlarmType=type,
            ChatID=chat_id,
            ExchangeID=exchange_id,
            BaseSymbol=base_symbol,
            QuoteSymbol=quote_symbol,
            AlarmQuantity=quantity,
            IsEnabled=is_enabled,
            IsChannel=is_channel
        )

    
    def add_chat(self, chat_id: int, alarm_option=True) -> int:
        if self.is_exists(table_name='Chat', primary_key=chat_id):
            raise self.ExistingDataError

        self.insert(table_name='Chat', ChatID=chat_id, Alarmoption=alarm_option)
        return chat_id

    
    def add_channel(self, channel_id: int, name: str, chat_id: int, alarm_option=True) -> int:
        if self.is_exists(table_name='Channel', primary_key=channel_id):
            raise self.ExistingDataError

        self.insert(table_name='Channel', ChannelID=channel_id, ChannelName=name, ChatID=chat_id, AlarmOption=alarm_option)
        return channel_id


    def add_alarm(self, type: str, chat_id: int, exchange_id: int, base_symbol: str, quote_symbol: str, quantity: float, is_channel: bool) -> int:
        alarm_id = self.insert('Alarm',
            AlarmType=type,
            ChatID=chat_id,
            ExchangeID=exchange_id,
            BaseSymbol=base_symbol,
            QuoteSymbol=quote_symbol,
            AlarmQuantity=quantity,
            IsEnabled=True,
            IsChannel=is_channel
        )

        return alarm_id


    def delete_chat(self, chat_id: int):
        for channel in self.get_channels(chat_id=chat_id):
            channel_id = channel.id
            self.delete_channel(channel_id)

        self.delete(table_name='Alarm', ChatID=chat_id)
        self.delete(table_name='Chat', ChatID=chat_id)


    def delete_channel(self, channel_id: int):
        self.delete(table_name='Alarm', ChatID=channel_id)
        self.delete(table_name='Channel', ChannelID=channel_id)

    
    def delete_alarm(self, alarm_id: int):
        self.delete(table_name='Alarm', AlarmID=alarm_id)