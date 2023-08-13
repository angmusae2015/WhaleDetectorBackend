# sqlite3 데이터베이스 파일 생성

import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()


# 거래소 정보 테이블
cur.execute("""CREATE TABLE Exchange (
    ExchangeID INTEGER PRIMARY KEY AUTOINCREMENT,
    ExchangeName TEXT NOT NULL,
    ExchangeEndpoint TEXT NOT NULL
);""")
cur.execute("""INSERT INTO Exchange (ExchangeName, ExchangeEndpoint) VALUES ("업비트", "/upbit");""")
cur.execute("""INSERT INTO Exchange (ExchangeName, ExchangeEndpoint) VALUES ("바이낸스", "/binance");""")


# 화폐 정보 캐시 테이블
cur.execute("""CREATE TABLE Currency (
    CurrencySymbol TEXT PRIMARY KEY,
    EnglishName TEXT,
    KoreanName TEXT
);""")


# 채팅 설정 테이블
cur.execute("""CREATE TABLE Chat (
    ChatID INTEGER PRIMARY KEY,
    AlarmOption BOOLEAN NOT NULL DEFAULT 1
);""")


# 채널 정보 테이블
cur.execute("""CREATE TABLE Channel (
    ChannelID INTEGER PRIMARY KEY,
    ChannelName TEXT NOT NULL,
    ChatID INTEGER NOT NULL,
    AlarmOption BOOLEAN NOT NULL DEFAULT 1,

    FOREIGN KEY (ChatID) REFERENCES Chat(ChatID) ON DELETE CASCADE
);""")
    
# 알림 설정 규칙 테이블
cur.execute("""CREATE TABLE Alarm (
    AlarmID INTEGER PRIMARY KEY AUTOINCREMENT,
    AlarmType TEXT NOT NULL,
    ChatID INTEGER NOT NULL,
    ExchangeID INTEGER NOT NULL,
    BaseSymbol TEXT NOT NULL,
    QuoteSymbol TEXT NOT NULL,
    AlarmQuantity REAL NOT NULL,
    IsEnabled BOOLEAN NOT NULL DEFAULT 1,
    IsChannel BOOLEAN NOT NULL
);""")

conn.commit()
conn.close()