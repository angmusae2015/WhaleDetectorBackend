# 데이터베이스 API
import os
import json
from typing import Union, List

from connection import connect


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


    def __init__(self, database_url: str, debug=False, test=False):
        self.conn = connect(database_url)
        self.debug = debug
        self.test = test

        self.conn.autocommit = True

    
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
            cursor.execute(query)

            try:
                column = [tu[0] for tu in cursor.description]
                result = cursor.fetchall()

            except TypeError:
                return ResultSet([], [])

            else:
                return ResultSet(column, result)    # 결과 집합 반환

    
    # 해당 테이블의 컬럼명 반환
    def get_columns(self, table_name: str) -> list:
        result_set = self.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}';")

        return result_set.keys()
        
    
    # SELECT문 실행
    def select(self, table_name: str, **kwargs) -> ResultSet:
        query = f"SELECT * FROM {table_name}"
    
        # 조건 지정
        if kwargs != {}:
            query += " WHERE " + self.to_parameter_statement(**kwargs)

        result_set = self.execute(query)

        return result_set   # 결과 집합 반환

    
    # INSERT문 실행
    def insert(self, table_name: str, **kwargs) -> int:
        columns = tuple(kwargs.keys())
        values = tuple(kwargs.values())

        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({self.to_parameter_statement(', ', *values)}) RETURNING {table_name}ID;"
        
        result_set = self.execute(query)
        
        return result_set.column[0]
    
    
    # UPDATE문 실행
    def update(self, table_name: str, primary_key, **kwargs):
        primary_key_column = self.get_columns(table_name)[0]
        query = f"UPDATE {table_name} SET {', '.join(columns)} WHERE {primary_key_column}={self.to_comparison_value(primary_key)}"

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
        
        query = f"SELECT EXISTS(SELECT {table_name}id FROM {table_name} WHERE {condition_state});"
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