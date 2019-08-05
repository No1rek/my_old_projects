#!/usr/bin/env python

from pyrogram import Client
import re
import json
import signal
import sys
import time
import configparser
from cryptopia_api import Api
import sys
from testing import *

class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


# *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#
def parseCoin(s):
    m = re.search('The coin to pump is: . (.+?) . ', s)
    if m and 'PUMP STARTS'.lower() in s.lower() and 'Cryptopia'.lower() in s.lower():
        return m.group(1).strip()
    return ''


# Загружается конфиг
def load_cfg(var, n):
    global config
    try:
        value = config['config'][n]
        if str(value).lower() == 'true' \
                or str(value).lower() == 'false':
            return bool(str(value).lower() == 'true')
        return type(var)(value)
    except KeyError:
        return var


# Get these from (link here)
def sigint_handler():
    """Handler for ctrl+c"""
    print('\n[!] CTRL+C pressed. Exiting...')
    client.stop()
    sys.exit(0)


# -----------------------------------------------------------------------------------------------------------------------
# @callback_wrapper(100,150,1600,300,0.00000433)
def callback(update, *args, **kwargs):
    try:
        API = kwargs['API']
    except:
        pass

    # Записывает в истории торгов момент начала пампа
    API.pump_start_id = len(API.history) - 1

    PUMP_COIN = ''

    # Парсится сообщение, ищется монета
    if isinstance(update, str):
        PUMP_COIN = update
    else:
        try:
            update = json.loads(str(update).translate(non_bmp_map))
            if update['_'] == 'types.Update':
                for u in update['updates']:
                    if u['_'] == 'types.UpdateNewChannelMessage' and update['chats'][0]['title'] == Channel:
                        msg = u['message']['message']
                        PUMP_COIN = parseCoin(msg)
                        print(PUMP_COIN)
        except Exception:
            print(update)
            return
    if PUMP_COIN == '':
        return

    # Получает инфу о рынке
    API.currency = PUMP_COIN
    COIN_PRICE = API.get_price(PUMP_COIN + "/BTC")
    # Получает цену
    ASK_PRICE = COIN_PRICE['AskPrice']

    '''
    Можно заменить на какую-то более гибку покупку
    '''
    # Цена покупки в процентах от текущего курса - купить 150%
    ASK_BUY = ASK_PRICE + (PUMP_BUY / 100 * ASK_PRICE)

    print('\nUsing {:.8f} BTC to buy {} .'.format(PUMP_BALANCE, PUMP_COIN))
    print('Current ASK price for {} is {:.8f} BTC.'.format(PUMP_COIN, ASK_PRICE))
    print('\nASK + {}% (your specified buy point) for {} is {:.8f} \
            BTC.'.format(PUMP_BUY, PUMP_COIN, ASK_BUY))

    # calculates the number of PUMP_COIN(s) to buy, taking into
    # consideration Cryptopia's 0.20% fee.
    NUM_COINS = (PUMP_BALANCE - (PUMP_BALANCE * 0.00201)) / ASK_BUY

    BUY_PRICE = ASK_BUY * NUM_COINS
    API.buy_price = ASK_BUY * 1.00401

    print('\n[+] Buy order placed for {:.8f} {} coins at {:.8f} BTC \
		   each for a total of {} BTC'.format(NUM_COINS, PUMP_COIN, ASK_BUY, BUY_PRICE))

    '''
    Вот тут можно переписать, чтобы оно перезакупалось если опоздало
    '''
    # Если настоящий режим, то совершить покупку валюты
    if ALLOW_ORDERS:
        TRADE, ERROR = API.submit_trade(PUMP_COIN + '/BTC', 'Buy', ASK_BUY, NUM_COINS)
        if ERROR is not None:
            print(ERROR)
            return
        print(TRADE)
    else:
        print("[!] Training Mode Active. No real orders are being placed.")

    '''
    продажа
    '''
    # Это для теста
    API.time_start = time.time()
    # # # # # # # #
    API.trade(PUMP_COIN, NUM_COINS, ALLOW_ORDERS)


if __name__ == '__main__':
    # Чтобы смотреть лог разных потоков непосредственно во время их выполнения
    sys.stdout = Unbuffered(sys.stdout)
    # Эмодзи
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

    Channel = 'Test Channel'

    # Загружается конфиг
    config = configparser.ConfigParser()
    config.read('config.ini')

    KEY = config['config']['KEY']
    SECRET = config['config']['SECRET']
    PHONE = config['config']['PHONE']

    # Выставляются значения по умолчанию
    PumpSum = 0.0
    PUMP_BALANCE = 0.0
    manual = False
    PUMP_BUY = 5.0

    PumpSum = load_cfg(PumpSum, 'PumpSum')
    PUMP_BALANCE = load_cfg(PUMP_BALANCE, 'PUMP_BALANCE')
    Channel = load_cfg(Channel, 'Channel')
    if str(config['config']['manual']).lower() == 'true':
        manual = True
    PUMP_BUY = load_cfg(PUMP_BUY, 'PUMP_BUY')

    THREADS = 100
    # setup api
    API = Api(KEY, SECRET, THREADS, logging=True)

    '''
    Запускаем потоки для записи баланса и данных рынка
    '''
    API.balance_record_active = True
    thread_id = API.add_task(API.balance_record, name='BalanceRecord')
    API.execute(thread_id)

    API.history_record_active = True
    thread_id = API.add_task(API.history_record, name='HistoryRecord')
    API.execute(thread_id)

    # Нужно, чтобы получить балансы и всю фигню, чтобы потом не возникало ошибок
    time.sleep(5)

    # Set to True to enable limit trading...
    ALLOW_ORDERS = False

    signal.signal(signal.SIGINT, sigint_handler)
    print('Crypto Crew Technologies Welcomes you to our Pump Trade Bot!')
    print('\nBuy and Sell orders will be instantly placed on Cryptopia at \
    a specified % above the ASK price.\n')
    TRAINING = input("   Live Mode (1) = Real orders will be placed.'\n\
    Training Mode (2) = No real orders will be placed.\n\n\
    Enter 1 for Live Mode or 2 for Training Mode - (1 or 2) ?: ")
    if TRAINING == "2":
        ALLOW_ORDERS = False
        print('\nTraining Mode Active! No real orders will be placed.')
        print('\nPress CTRL+C to exit at anytime.\n')
    else:
        ALLOW_ORDERS = True
        print('\nLive Mode Active! Real orders will be placed.\n\n\
    Press CTRL+C to exit at anytime.\n')
    print('You have {} BTC available.'.format(API.get_coin_balance('BTC')['Available']))

    while PUMP_BALANCE <= 0:
        PUMP_BALANCE = float(input("How much BTC would you like to use?: "))
        while PUMP_BALANCE > API.get_coin_balance('BTC')['Available']:
            print('You can\'t invest more than {}'.format(API.get_coin_balance('BTC')['Available']))
            PUMP_BALANCE = float(input("How much BTC would you like to use?: "))

    if manual:
        print('\n***Wait input data***\n')
        while True:
            try:
                PUMP_COIN = input().rstrip(' \t\r\n\0').upper()
                if PUMP_COIN != '':
                    print(PUMP_COIN)
                    callback(PUMP_COIN)
                    break
            except Exception as e:
                print(e)
            time.sleep(0.01)
    else:
        # Инициализация клиента
        client = Client(
            session_name="pyro",
            phone_number=PHONE,
            phone_code=input("code: "),
        )

        client.set_update_handler(callback)
        client.start()
        print(client.get_me().user)
        client.idle()
