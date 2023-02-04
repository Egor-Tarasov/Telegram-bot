from settings import *
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from data_user import *
from datetime import timedelta, date
import re
import hotels


def delete_r(data):
    result = re.compile(r'-')
    return result.sub(' ', data)


def valid_data(string):
    if string[0] == '0':
        string = int(string[1])
        return string
    else:
        string = int(string)
        return string


def set_arrival_date(message):
    user = User.get_user(message.from_user.id)
    bot.send_message(message.chat.id, "Введите дату заезда")
    calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                              current_date=date.today(),
                                              min_date=date.today(),
                                              max_date=date.today() + timedelta(days=365),
                                              locale="ru").build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def handle_arrival_date(call):
    user = User.get_user(call.from_user.id)
    result, key, step = DetailedTelegramCalendar(calendar_id=1,
                                                 current_date=date.today(),
                                                 min_date=date.today(),
                                                 max_date=date.today() + timedelta(days=365),
                                                 locale="ru").process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        user.arrival_date = result
        user.check_in_date['year'] = valid_data(delete_r(str(user.arrival_date)[0:4]))
        user.check_in_date['month'] = valid_data(delete_r(str(user.arrival_date)[5:7]))
        user.check_in_date['day'] = valid_data(delete_r(str(user.arrival_date)[8:]))
        bot.edit_message_text(f"Дата заезда {user.arrival_date}",
                              call.message.chat.id,
                              call.message.message_id)

        bot.send_message(user.user_id, "Введите дату выезда")
        calendar, step = DetailedTelegramCalendar(calendar_id=2,
                                                  min_date=user.arrival_date + timedelta(days=1),
                                                  max_date=user.arrival_date + timedelta(days=365),
                                                  locale="ru").build()
        bot.send_message(user.user_id,
                         f"Select {LSTEP[step]}",
                         reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def handle_departure_date(call):
    user = User.get_user(call.message.chat.id)
    result, key, step = DetailedTelegramCalendar(calendar_id=2,
                                                 min_date=user.arrival_date + timedelta(days=1),
                                                 max_date=user.arrival_date + timedelta(days=365),
                                                 locale="ru").process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}", user.user_id, call.message.message_id, reply_markup=key)
    elif result:
        user.departure_date = result
        user.check_out_date['year'] = valid_data(delete_r(str(user.departure_date)[0:4]))
        user.check_out_date['month'] = valid_data(delete_r(str(user.departure_date)[5:7]))
        user.check_out_date['day'] = valid_data(delete_r(str(user.departure_date)[8:]))
        bot.send_message(call.message.chat.id, f"Дата выезда {user.departure_date}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return hotels.show_or_not_to_show_hotels_photo(call.message)