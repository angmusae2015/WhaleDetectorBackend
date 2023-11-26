import json

from connection import connect

conn = None
with open('./token.json', 'r') as file:
    tokens = json.load(file)
    conn = connect(tokens['database_url'])

conn.autocommit = True
cur = conn.cursor()

# 거래소 정보 테이블
cur.execute("""CREATE TABLE exchange (
    exchange_id SERIAL PRIMARY KEY,
    exchange_name TEXT NOT NULL
);""")
cur.execute("""INSERT INTO exchange (exchange_name) VALUES ('업비트');""")
cur.execute("""INSERT INTO exchange (exchange_name) VALUES ('바이낸스');""")

# 채팅 정보 테이블
cur.execute("""CREATE TABLE chat (
    chat_id BIGINT PRIMARY KEY
);""")

# 채널 정보 테이블
cur.execute("""CREATE TABLE channel (
    channel_id BIGINT PRIMARY KEY,
    channel_name TEXT NOT NULL
);""")

# 알림 규칙 테이블
cur.execute("""CREATE TABLE condition (
    condition_id SERIAL PRIMARY KEY,
    whale JSON,
    tick JSON,
    bollinger_band JSON,
    rsi JSON
);""")
    
# 알림 정보 테이블
cur.execute("""CREATE TABLE alarm (
    alarm_id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    exchange_id INTEGER NOT NULL,
    base_symbol TEXT NOT NULL,
    quote_symbol TEXT NOT NULL,
    condition_id INTEGER NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    FOREIGN KEY (exchange_id) REFERENCES exchange(exchange_id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channel(channel_id) ON DELETE CASCADE,
    FOREIGN KEY (condition_id) REFERENCES condition(condition_id) ON DELETE CASCADE
);""")

conn.commit()
conn.close()