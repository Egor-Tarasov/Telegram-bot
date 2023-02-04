import telebot
import pymysql
from peewee import *


bot = telebot.TeleBot('YOUR_API_KEY')

headers: dict = {
    'content-type': 'application/json',
    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
    'x-rapidapi-key': 'YUOR_RAPIDAPI_KEY'
}


my_db = MySQLDatabase('db_root',
                      user='root',
                      password='1111-password',
                      host='localhost',
                      port=3306)
