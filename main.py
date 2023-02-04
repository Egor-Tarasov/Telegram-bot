import hotels
import history
from datetime import datetime
from settings import *
from data_user import *


@bot.message_handler(content_types=['text'])
def get_started(message) -> None:
    """
    Данная функция обрабатывает сообщения пользователя.
    :param message:
    :return: None
    """
    user = User.get_user(message.from_user.id)
    if message.text == "/start":
        return bot.send_message(user.user_id,
                                "Добрый день! \nЯ - бот по поиску отелей\n"
                                "Для получения информации о командах нажмите /help")

    elif message.text == "/help":
        bot.send_message(user.user_id,
                         "Сведения о командах\n/help - помощь по командам\n"
                         "/lowprice — вывод самых дешёвых отелей в городе\n"
                         "/highprice — вывод самых дорогих отелей в городе\n"
                         "/bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра\n"
                         "/history — вывод истории поиска отелей")

    elif message.text == "/lowprice" or message.text == "/highprice" or message.text == "/bestdeal":
        user.request_time, user.command = datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message.text
        msg = bot.send_message(user.user_id, "Введите город")
        bot.register_next_step_handler(msg, hotels.find_location)

    elif message.text == "/history":
        history.show_history(message)

    else:
        bot.send_message(message.chat.id, "Я Вас не понимаю.\nВведите команду: /help")


if __name__ == '__main__':
    history.create_db()
    bot.polling(none_stop=True)