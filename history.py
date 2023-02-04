from data_user import User
from settings import *
from peewee import Model
import pymysql
import telebot


class BaseModel(Model):
    class Meta:
        database = my_db


class UserData(BaseModel):
    user_telegram_id = IntegerField()
    user_command = CharField()
    user_time_request = CharField()
    user_hotels_list = CharField()


def create_db() -> None:
    """
    Функция создает базу данных, если она отсутствует.
    :return:
    """
    try:
        my_db.connect()
        UserData.create_table()
    except InternalError as px:
        print(str(px))


def add_user_data(user_telegram_id, command, request_time, text_for_database) -> None:
    """
    Функция создает запись в базе данных.
    :param user_telegram_id:
    :param command:
    :param request_time:
    :param text_for_database:
    :return:
    """

    with my_db:
        UserData.create(user_telegram_id=user_telegram_id,
                        user_command=command,
                        user_time_request=request_time,
                        user_hotels_list=text_for_database
                        )


def to_use_literals(string: str) -> str:
    """
    Функция принимает значение 'название отелей' из базы данных и в этом значении заменяет символ ; на литерал
    :param string:
    :return: string
    """
    return string.replace(';', '\n')


def show_history(message: telebot.types.Message) -> None:
    """
    Функция, которая отправляет пользователю историю запросов.
    :param message:
    :return: None
    """

    user = User.get_user(message.from_user.id)
    with my_db:
        for data in UserData.select().where(UserData.user_telegram_id == user.user_id):
            history_to_show = f"Команда: {data.user_command}\n" \
                              f"Дата и время обращения: {data.user_time_request}\n" \
                              f"Список найденных отелей:\n{to_use_literals(data.user_hotels_list)}"
            bot.send_message(user.user_id, history_to_show)