from telebot import TeleBot


def get_token(file_path: str):
    with open(file_path, 'r') as file:
        token = file.read().strip()
    return token


def get_bot(file_path: str) -> TeleBot:
    token = get_token(file_path)

    return TeleBot(token)