import telebot
import pymysql
from peewee import *


bot = telebot.TeleBot('5822209451:AAH2m83luZY2HHC8WrO52SOcpSJp6sCi_Os')

headers: dict = {
    'content-type': 'application/json',
    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
    'x-rapidapi-key': 'c02baf658emsh19fca9c5f2e0924p1ccd3djsn07c2983e5bf9'
}


my_db = MySQLDatabase('db_root',
                      user='root',
                      password='1111-password',
                      host='localhost',
                      port=3306)
