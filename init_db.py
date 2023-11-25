import json

from connection import connect

conn = None
with open('./token.json', 'r') as file:
    tokens = json.load(file)
    conn = connect(tokens['database_url'])

conn.autocommit = True
cur = conn.cursor()

# 거래소 정보 테이블
cur.execute("""CREATE TABLE Exchange (
    ExchangeID SERIAL PRIMARY KEY,
    ExchangeName TEXT NOT NULL
);""")
cur.execute("""INSERT INTO Exchange (ExchangeName) VALUES ('업비트');""")
cur.execute("""INSERT INTO Exchange (ExchangeName) VALUES ('바이낸스');""")

# 채팅 설정 테이블
cur.execute("""CREATE TABLE Chat (
    ChatID INTEGER PRIMARY KEY
);""")

# 채널 정보 테이블
cur.execute("""CREATE TABLE Channel (
    ChannelID INTEGER PRIMARY KEY,
    ChannelName TEXT NOT NULL
);""")
    
# 알림 설정 규칙 테이블
cur.execute("""CREATE TABLE Alarm (
    AlarmID SERIAL PRIMARY KEY,
    ChannelID INTEGER NOT NULL,
    ExchangeID INTEGER NOT NULL,
    BaseSymbol TEXT NOT NULL,
    QuoteSymbol TEXT NOT NULL,
    AlarmCondition JSON NOT NULL,
    IsEnabled BOOLEAN NOT NULL DEFAULT TRUE,

    FOREIGN KEY (ExchangeID) REFERENCES Exchange(ExchangeID) ON DELETE CASECADE,
    FOREIGN KEY (ChannelID) REFERENCES Channel(ChannelID) ON DELETE CASCADE
);""")

conn.commit()
conn.close()