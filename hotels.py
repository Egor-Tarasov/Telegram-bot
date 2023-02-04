from telebot import types
from settings import bot, headers
import requests
import re
import json
from data_user import *
import calendars
import history
from datetime import datetime
import telebot


def delete_spans(data: str) -> str:
    """
    Функция, удаляющая спецсимволы HTML.
    :param data: строка, содержащая теги HTML
    :return: строка без HTML тегов
    """
    result = re.compile(r'<.*?>')
    return result.sub('', data)


def modify_number(number: str) -> int or float:
    """
    Функция принимает число с типом данных str и заменяет символ запятой на точку.
    :param number: целочисленное или вещественное число с запятой
    :return: целочисленное или вещественное число в соответствии с правилами ЯП Python
    """

    if re.sub(",", ".", number.split()[0], 1).isdigit():
        modified_num = int(re.sub(",", ".", number.split()[0], 1))
    else:
        modified_num = float(re.sub(",", ".", number.split()[0], 1))
    return modified_num


def modify_price(num: str) -> int:
    """
    Т.к. Rapid API возвращает значение стоимости с разделителями в виде запятой,
    данная функция предназначена для удаления запятой.
    :param num: строка
    :return: число
    """
    return int(re.sub(r'[^0-9]+', "", num))


def add_indent(s: int) -> str:
    """
    Функция в значение стоимости добавляет разделитель для удобства чтения информации.
    :param s: число
    :return: строка
    """
    return '{0:,}'.format(s).replace(',', ' ')


def is_number_float(line: str) -> bool:
    """
    Функция проверяет, является ли число float.
    :param line: строка
    :return: True or False
    """

    i = re.match(r'\d*\.?\d+', line)
    if i:
        return i.group() == line
    return False


def calculate_price_for_certain_period(date_1: str, date_2: str, price_for_night: str) -> int:
    """
    price_for_certain_period
    Функция считает стоимость проживания в отеле за ночь.
    :param date_1: дата заезда
    :param date_2: дата выезда
    :param price_for_night: стоимость проживания за ночь
    :return: стоимость проживания за весь период
    """

    d_1 = datetime.strptime(str(date_1), "%Y-%m-%d")
    d_2 = datetime.strptime(str(date_2), "%Y-%m-%d")
    date_delta = int((d_2 - d_1).days)
    return int(price_for_night) * date_delta


def request_to_api(url: str, headers: dict, querystring: dict) -> dict or None:
    """
    Функция, производящая запрос к API.
    :param url: ссылка
    :param headers: headers
    :param querystring: parameters
    :return:
    """

    response = requests.request("GET", url,
                                headers=headers,
                                params=querystring
                                )
    if response.status_code == requests.codes.ok:
        return response.text


def request_to_api_post(url: str, payload: dict, headers: dict) -> dict or None:
    """
    Функция, производящая запрос к API.
    :param url: ссылка
    :param payload: parameters
    :param headers: headers
    :return:
    """

    response = requests.request("POST", url,
                                json=payload,
                                headers=headers
                                )
    if response.status_code == requests.codes.ok:
        return response.text


def find_location(message: telebot.types.Message) -> telebot.types.Message or None:
    """
    Функция для определения локации поиска.
    :param message:
    :return:
    """
    user = User.get_user(message.from_user.id)
    user.city = message.text
    markup = types.InlineKeyboardMarkup()

    url_for_destination_id = "https://hotels4.p.rapidapi.com/locations/v2/search"

    querystring_for_destination_id = {"query": user.city,
                                      "locale": "ru_RU",
                                      "currency": "USD"
                                      }

    response = request_to_api(url=url_for_destination_id,
                              headers=headers,
                              querystring=querystring_for_destination_id)

    if not response:
        bot.send_message(message.chat.id, "Произошла ошибка.\nПопробуйте снова.")
    else:
        result = json.loads(response)["suggestions"][0]["entities"]
        if result:
            caption_dict_with_geo_id = dict()
            for i_elem in result:
                if "<" in i_elem.get("caption"):
                    cap = delete_spans(i_elem.get("caption"))
                    if (user.city.title() in cap) or (user.city.lower() in cap):
                        caption_dict_with_geo_id[cap] = i_elem.get("geoId")

            if len(caption_dict_with_geo_id) < 1:
                bot.send_message(message.chat.id, "По Вашему запросу ничего не найдено.\n"
                                                  "Попробуйте еще раз.")
                msg = bot.send_message(user.user_id, "Введите город")
                return bot.register_next_step_handler(msg, find_location)

            for elem in caption_dict_with_geo_id:
                markup.add(types.InlineKeyboardButton(elem, callback_data=caption_dict_with_geo_id[elem]))

            bot.send_message(message.chat.id, "Выберите локацию", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "По Вашему запросу ничего не найдено.\n"
                                              "Попробуйте еще раз.")
            msg = bot.send_message(user.user_id, "Введите город")
            return bot.register_next_step_handler(msg, find_location)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        user.geo_id = call.data
        msg = bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text="Введите кол-во отелей (максимум - 10):",
                                    reply_markup=None)

        bot.register_next_step_handler(msg, set_hotels_number)


def set_hotels_number(message: telebot.types.Message) -> telebot.types.Message or None:
    """
    Сеттер для кол-ва выводимых отелей.
    Проверяет, правильно ли пользователь ввел кол-во отелей для вывода.
    Значение выводимых отелей должно быть числом и не должно превышать 10.
    :param message:
    :return:
    """
    user = User.get_user(message.from_user.id)

    if message.text.isdigit():
        if int(message.text) > 10:
            bot.send_message(message.chat.id, "Вы ввели значение, превышающее 10")
            msg = bot.send_message(message.chat.id, "Введите кол-во отелей (максимум - 10):")
            return bot.register_next_step_handler(msg, set_hotels_number)

        user.hotels_number_to_show = int(message.text)
        if user.command == "/lowprice" or user.command == "/highprice":
            return calendars.set_arrival_date(message)
        msg = bot.send_message(message.chat.id, "Введите диапазон цен (пример ввода: 50-150) USD:")
        return bot.register_next_step_handler(msg, set_price_range)

    msg = bot.send_message(message.chat.id, "Ошибка ввода. Необходимо ввести число от 1 до 10.")
    return bot.register_next_step_handler(msg, set_hotels_number)


# ----------------------------------------------------------------------------------------------------------------------
"""Функции для команды Best Deal: set_price_range"""


def set_price_range(message: telebot.types.Message) -> None:
    """
    Сеттер для диапазона цен.
    Проверяет, правильно ли пользователь ввел диапазон цен в соответствии с примером.
    :param message:
    :return:
    """
    user = User.get_user(message.from_user.id)
    price_range = message.text.split("-")
    if len(price_range) == 2:
        if price_range[0].isdigit() and price_range[1].isdigit():
            if int(price_range[0]) < int(price_range[1]):
                price_min, price_max = int(price_range[0]), int(price_range[1])
            else:
                price_min, price_max = int(price_range[1]), int(price_range[0])
            user.min_price, user.max_price = price_min, price_max
            return calendars.set_arrival_date(message)

    else:
        bot.send_message(message.chat.id, "Ошибка ввода. Попробуйте снова.")
        msg = bot.send_message(message.chat.id, "Введите диапазон цен (пример ввода: 50-150) USD:")
        return bot.register_next_step_handler(msg, set_price_range)


#  ---------------------------------------------------------------------------------------------------------------------


def show_or_not_to_show_hotels_photo(message: telebot.types.Message) -> None:
    """
    Данная функция спрашивает у пользователя: показать фото?
    :param message:
    :return:
    """

    photo_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    photo_markup.add("Да", "Нет")
    msg = bot.send_message(message.chat.id, "Показать фото?", reply_markup=photo_markup)
    bot.register_next_step_handler(msg, photos_handler)


def photos_handler(message: telebot.types.Message) -> None:
    """
    Функция, обрабатывающая ответ пользователя из функции show_or_not_to_show_hotels_photo
    :param message:
    :return:
    """

    user = User.get_user(message.from_user.id)

    if message.text == "Да":
        user.photos_uploaded["status"] = True
        msg = bot.send_message(message.chat.id, "Сколько фото загрузить? (максимум - 4)")
        bot.register_next_step_handler(msg, photos_number_setter)
    elif message.text == "Нет":
        user.photos_uploaded["status"] = False
        find_hotels_id(message)


def photos_number_setter(message: telebot.types.Message) -> None:
    """
    Сеттер. Проверяет, правильно ли пользователь ввел значение кол-ва выводимых фото
    :param message:
    :return:
    """
    user = User.get_user(message.from_user.id)
    if message.text.isdigit():
        if int(message.text) > 4:
            bot.send_message(message.chat.id, "Вы ввели значение, превышающее 4.\n"
                                              "Кол-во фото будет задано по умолчанию - 4.")
            user.photos_uploaded["number_of_photos"] = 4
        else:
            user.photos_uploaded["number_of_photos"] = int(message.text)
        find_hotels_id(message)
    else:
        bot.send_message(message.chat.id, "Значение кол-ва фото должно быть числом.")
        msg = bot.send_message(message.chat.id, "Сколько фото загрузить? (максимум - 4)")
        return bot.register_next_step_handler(msg, photos_number_setter)


def find_hotels_id(message: telebot.types.Message):
    """
    На первоначальном этапе функция делает запрос к API.
    В случае получения положительного статуса запроса функция собирает данные по каждому отелю.
    Далее проверяется статуса показа фотографий отеля.
    Если условие вывода фото user.photos_uploaded["status"] == False, то
    в бот отправляет пользователю собранные сведения об отелях.
    В противном случаи, вызывается функция получения фотографий отелей (get_photos).
    :param message:
    :return:
    """

    user = User.get_user(message.from_user.id)
    bot.send_message(message.chat.id, "Идет поиск...")

    url_for_hotels_id_list = "https://hotels4.p.rapidapi.com/properties/v2/list"

    if user.command == "/lowprice" or user.command == "/highprice":
        payload_for_hotels_list = {"currency": "USD",
                                   "eapid": 1,
                                   "locale": "ru_RU",
                                   "siteId": 300000001,
                                   "destination": {"regionId": user.geo_id},
                                   "checkInDate": user.check_in_date,
                                   "checkOutDate": user.check_out_date,
                                   "rooms": [{"adults": 1}],
                                   "resultsStartingIndex": 0,
                                   "resultsSize": user.hotels_number_to_show if user.command == "/lowprice" else 200,
                                   "sort": "PRICE_LOW_TO_HIGH",
                                   "filters": {"price": {"max": 200, "min": 1}}
                                   }

    else:
        payload_for_hotels_list = {"currency": "USD",
                                   "eapid": 1,
                                   "locale": "ru_RU",
                                   "siteId": 300000001,
                                   "destination": {"regionId": user.geo_id},
                                   "checkInDate": user.check_in_date,
                                   "checkOutDate": user.check_out_date,
                                   "rooms": [{"adults": 1}],
                                   "resultsStartingIndex": 0,
                                   "resultsSize": 200,
                                   "sort": "DISTANCE",
                                   "filters": {"price": {"max": user.max_price, "min": user.min_price}}
                                   }

    response_for_hotels_id_list = request_to_api_post(url=url_for_hotels_id_list,
                                                      payload=payload_for_hotels_list,
                                                      headers=headers
                                                      )

    if user.command:
        if user.command == "/lowprice" or user.command == "/bestdeal":
            result_of_hotels_id_list = json.loads(response_for_hotels_id_list)["data"]["propertySearch"]["properties"][
                                      0:user.hotels_number_to_show]
        else:
            result_of_hotels_id_list = json.loads(response_for_hotels_id_list)["data"]["propertySearch"]["properties"][
                                       ::-1][0:user.hotels_number_to_show]

        user.list_of_hotels_id = {i.get("id"): {
                                       "hotel_name": i.get("name"),
                                       "distance_from_center": i["destinationInfo"]["distanceFromDestination"].get(
                                           "value"),
                                       "price_for_night": modify_price(i["price"]["lead"].get("formatted")),
                                       "photos": []} for i in result_of_hotels_id_list
                                  }
    for id_hotels in user.list_of_hotels_id:

        url_for_hotels_address = "https://hotels4.p.rapidapi.com/properties/v2/get-summary"

        payload_for_hotels_address = {"currency": "RUB",
                                      "eapid": 1,
                                      "locale": "ru_RU",
                                      "siteId": 300000001,
                                      "propertyId": id_hotels
                                      }

        response_for_hotels_address = request_to_api_post(url=url_for_hotels_address,
                                                          payload=payload_for_hotels_address,
                                                          headers=headers
                                                          )

        result_of_hotels_address = \
        json.loads(response_for_hotels_address)["data"]["propertyInfo"]["summary"]["location"]["address"]

        user.list_of_hotels_id[id_hotels]["hotel_address"] = result_of_hotels_address.get("firstAddressLine")

    if user.photos_uploaded["status"] is False:
        text_for_database = ""
        for hotel in user.list_of_hotels_id:
            price_for_certain_period = calculate_price_for_certain_period(user.arrival_date,
                                                                          user.departure_date,
                                                                          user.list_of_hotels_id[hotel][
                                                                              'price_for_night'])
            bot.send_message(message.chat.id,
                             f"Отель: {user.list_of_hotels_id[hotel]['hotel_name']}\n"
                             f"Адрес: {user.list_of_hotels_id[hotel]['hotel_address']}\n"
                             f"Расстояние до центра: {user.list_of_hotels_id[hotel]['distance_from_center']} км.\n"
                             f"Период проживания: с {user.arrival_date} по {user.departure_date}\n"
                             f"Цена за указанный период проживания:"
                             f" {add_indent(price_for_certain_period)} USD.\n"
                             f"Цена за ночь: {add_indent(user.list_of_hotels_id[hotel]['price_for_night'])} USD.")

            text_for_database += f"{user.list_of_hotels_id[hotel]['hotel_name']};"

        history.add_user_data(user.user_id, user.command, user.request_time, text_for_database)
        return bot.send_message(message.chat.id,
                                f"Поиск завершен.\nНайдено предложений: {len(user.list_of_hotels_id)}")
    return get_photos(message)
    # else:
    #     return bot.send_message(message.chat.id, "По Вашему запросу ничего не найдено")


def get_photos(message: telebot.types.Message):
    """
    В случае условия user.photos_uploaded["status"] == True
    функция, которая получает ссылки на фото отелей и добавляет их в атрибут класса User.
    :param message:
    :return:
    """

    user = User.get_user(message.from_user.id)

    for hotel_data in user.list_of_hotels_id:

        url_for_hotels_photos = "https://hotels4.p.rapidapi.com/properties/v2/get-offers"
        payload_for_hotels_photos = {
                                    "currency": "USD",
                                    "eapid": 1,
                                    "locale": "ru_RU",
                                    "siteId": 300000001,
                                    "propertyId": hotel_data,
                                    "checkInDate": user.check_in_date,
                                    "checkOutDate": user.check_out_date,
                                    "destination": {"regionId": user.geo_id},
                                    "rooms": [{"adults": 1}]
        }

        response_for_hotels_photos = request_to_api_post(url=url_for_hotels_photos,
                                                         payload=payload_for_hotels_photos,
                                                         headers=headers
                                                         )

        if not response_for_hotels_photos:
            return bot.send_message(message.chat.id, "Произошла ошибка.")
        else:
            result_of_hotels_photos = json.loads(response_for_hotels_photos)["data"]["propertyOffers"]["units"][1][
                "unitGallery"]["gallery"]

            if len(result_of_hotels_photos) >= user.photos_uploaded["number_of_photos"]:
                result_of_hotels_photos = json.loads(response_for_hotels_photos)["data"]["propertyOffers"]["units"][
                                              1]["unitGallery"]["gallery"][0:user.photos_uploaded["number_of_photos"]]

            for hotel_photos in result_of_hotels_photos:
                photo_url = hotel_photos["image"]["url"]
                user.list_of_hotels_id[hotel_data]["photos"].append(photo_url)

    return show_final_data(message)


def show_final_data(message: telebot.types.Message):
    """
    Конечная функция: отправляет итоговую информацию пользователю.
    Итоговая информация имеет вид - альбом, состоящий из фотографий с подписью к первой фотографии.
    :param message:
    :return:
    """

    user = User.get_user(message.from_user.id)
    text_for_database = ""
    for hotel in user.list_of_hotels_id:
        price_for_certain_period = calculate_price_for_certain_period(user.arrival_date,
                                                                      user.departure_date,
                                                                      user.list_of_hotels_id[hotel][
                                                                          "price_for_night"])

        text = f"Отель: {user.list_of_hotels_id[hotel]['hotel_name']}\n"\
               f"Адрес: {user.list_of_hotels_id[hotel]['hotel_address']}\n"\
               f"Расстояние до центра: {user.list_of_hotels_id[hotel]['distance_from_center']} км.\n"\
               f"Период проживания: с {user.arrival_date} по {user.departure_date}\n"\
               f"Цена за указанный период проживания:"\
               f" {add_indent(price_for_certain_period)} USD.\n"\
               f"Цена за ночь: {add_indent(user.list_of_hotels_id[hotel]['price_for_night'])} USD."

        text_for_database += f"{user.list_of_hotels_id[hotel]['hotel_name']};"

        photos = [types.InputMediaPhoto(media=url, caption=text) if num == 0
                  else types.InputMediaPhoto(media=url)
                  for num, url in enumerate(user.list_of_hotels_id[hotel]["photos"])]

        bot.send_media_group(message.chat.id, photos)

    history.add_user_data(user.user_id, user.command, user.request_time, text_for_database)

    return bot.send_message(message.chat.id,
                            f"Поиск завершен.\nНайдено предложений: {len(user.list_of_hotels_id)}")