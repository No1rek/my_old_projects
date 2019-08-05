import sys, linecache
import pprint
import configparser, copy, time, threading, json, re, sys
from pyrogram import Client
from cryptopia_api import Api
from data_processing import DataProcessing
from indicators import *
from view import Form
from testing import TestApi


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))


def exception_handler(name):
    def decorator(function):
        def wrapper(*args, **kwargs):
            function.name = name
            try:
                result = function(*args, **kwargs)
            except Exception as e:
                print('Exception in function %s: ' % name, function.name)
                print(e)
                result = None
            return result

        return wrapper

    return decorator


class Bot:
    # @exception_handler('init')
    def __init__(self):
        self.RUNNING = False
        self.load_config()
        if self.test_mode:
            self.API = TestApi(self.KEY, self.SECRET, BOT=self)
        else:
            self.API = Api(self.KEY, self.SECRET)
        self.modify_api()
        self.data_processing = DataProcessing()
        # self.INDICATORS = [NeuralNetwork(self), Ladder(self)]
        self.INDICATORS = []

        self.VIEW = Form(self, INDICATORS=self.INDICATORS)

        self.VIEW.show()

    # @exception_handler('load_var')
    def load_var(self, var, n, section='settings'):
        try:
            value = self.config[section][n]
            if str(value).lower() == 'true' \
                    or str(value).lower() == 'false':
                return bool(str(value).lower() == 'true')
            return type(var)(value)
        except KeyError:
            return var

    # @exception_handler('load_config')
    def load_config(self):

        self.balances = []
        self.balance_last_update_time = 0
        self.history = []
        self.orders = []
        self.data_to_log = []
        self.task_pool = []
        self.currency = ''
        self.signals = []
        self.pump_start_id = 0

        self.start_price = 0.00000001
        # Цена покупки
        self.buying_price = 0.00000001
        self.current_price = 0.00000001
        self.profit = 0
        self.pump_btc_volume = 0
        self.orders = []

        # Это нужно потом перенести в конфиг
        self.orders_record_active = True
        self.orders_requests_per_second = 2

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.KEY = self.config['config']['KEY']
        self.SECRET = self.config['config']['SECRET']
        self.PHONE = self.config['config']['PHONE']
        self.Channel = self.config['config']['Channel']
        self.REGEXP = self.config['config']['regexp']

        # Устанавливаем значения по умолчанию для определения типа переменных
        PumpSum, PUMP_BALANCE, manual, PUMP_BUY, Channel, threads, minute_request_limit, \
        balance_requests_per_second, balance_record_active, history_length, history_record_active, pump_sell, pump_buy, \
        log_sleep_time, logging, log_file_name, time_sleep_to_get_data, allow_orders, test_mode, manual_sell, buy_price_max_point, \
        pump_sell_max, pump_buy_max \
            = 0.0, 0.0, False, 0.0, '', 0, 0, 0.0, False, 0, False, 0.0, 0.0, 0.0, False, '', 0.0, False, True, False, 0.0, 0.0, 0.0

        self.PUMP_BALANCE = self.load_var(PUMP_BALANCE, 'PUMP_BALANCE')
        self.manual = self.load_var(manual, 'manual')
        self.allow_orders = self.load_var(allow_orders, 'allow_orders')
        self.test_mode = self.load_var(allow_orders, 'test_mode')
        self.manual_sell = self.load_var(manual_sell, 'manual_sell')
        self.buy_price_max_point = self.load_var(buy_price_max_point, 'buy_price_max_point')

        self.threads = self.load_var(threads, 'threads')
        self.minute_request_limit = self.load_var(minute_request_limit, 'minute_request_limit')
        self.requests_sent_last_minute = 0

        self.active_threads = 0

        # Для ведения баланса
        self.balance_requests_per_second = self.load_var(balance_requests_per_second, 'balance_requests_per_second')
        self.balance_record_active = self.load_var(balance_record_active, 'balance_record_active')
        self.time_sleep_to_get_data = self.load_var(time_sleep_to_get_data, 'time_sleep_to_get_data')

        # Для сохранения истории торгов
        self.history_requests_per_second = self.load_var(threads, 'threads')
        self.history_length = self.load_var(history_length, 'history_length')
        self.history_record_active = self.load_var(history_record_active, 'history_record_active')

        # Продажа и покупка. Проценты считаются относительно цены которая была в момент начала пампа
        # соответствует history[self.pump_start_id]
        self.pump_sell = self.load_var(pump_sell,
                                       'pump_sell')  # Процент на который нужно опустить цену во время продажи
        self.pump_buy = self.load_var(pump_buy,
                                      'pump_buy')  # Цена закупки нужна для экстренной продажи, если памп не поднялся
        self.pump_sell_max = self.load_var(pump_sell_max,
                                           'pump_sell_max')
        self.pump_buy_max = self.load_var(pump_buy_max,
                                          'pump_buy_max')

        # Отвечает за запись лога
        self.logging = self.load_var(logging, 'logging')
        self.log_sleep_time = self.load_var(log_sleep_time, 'log_sleep_time')
        self.log_file_name = self.load_var(log_file_name, 'log_file_name')
        self.log_sleep_time = self.load_var(log_sleep_time, 'log_sleep_time')  # Секунд

    def run(self):
        self.RUNNING = True
        # Запускаем запись баланса
        if self.balance_record_active == True:
            thread_id = self.add_task(self.balance_record, name='BalanceRecord')
            self.execute(thread_id)

        if self.balance_record_active == True:
            thread_id = self.add_task(self.history_record, name='HistoryRecord')
            self.execute(thread_id)
            # self.nprint(self.time_sleep_to_get_data)
            # self.VIEW.root.after(round(self.time_sleep_to_get_data * 1000), None)
            self.wait_with_tk_update(self.time_sleep_to_get_data)
        # Запускаем поток для записи лога
        try:
            if self.logging:
                thread_id = self.add_task(self.log)
                self.execute(thread_id)
        except Exception as e:
            self.nprint(e)

        self.get_signal()

        # thread_id = self.add_task(self.get_signal)
        # self.execute(thread_id)
        #
        # # while self.RUNNING == True:
        # #     time.sleep(0.01)
        # #     self.VIEW.root.update()

    def wait_with_tk_update(self, delay):
        for i in range(round(delay * 100)):
            self.VIEW.root.update()
            time.sleep(0.01)

    def stop(self):
        self.RUNNING = False

    def modify_api(self):
        self.API.BOT = self
        self.API.minimal_order_value = 0.0005

        def get_markets_decorator(f):
            @exception_handler('get_markets')
            def new_get_markets(self, *args, **kwargs):
                try:
                    result = f(*args, **kwargs)
                    data = [{'time': str(time.time()), 'market': result}]
                    if len(self.BOT.currency) > 0:
                        data = {'time': str(time.time()),
                                'market': [self.BOT.get_price(self.BOT.currency + '/BTC', 0, data=data)]}
                    else:
                        data = data[0]
                    if len(self.BOT.history) < self.BOT.history_length:
                        # data = {'time': str(time.time()), 'market': result}
                        # if len(self.BOT.currency) > 0:
                        #     data = {'time': str(time.time()), 'market': [self.BOT.get_price(self.BOT.currency + '/BTC', 0, data=data)]}
                        markets = data
                        self.BOT.history.append(markets)
                    else:
                        del self.BOT.history[0]
                        markets = data
                        self.BOT.history.append(markets)
                        self.BOT.pump_start_id -= 1
                    if len(self.BOT.history) > 0 and len(self.BOT.currency):
                        # self.BOT.nprint(self.BOT.history[-1])
                        try:
                            self.BOT.current_price = round(float(
                                self.BOT.get_price(self.BOT.currency + '/BTC', i=-1, data=self.BOT.history)[
                                    'AskPrice']), 8)
                        except:
                            self.BOT.nprint(self.BOT.history[-1])
                        if self.BOT.pump_buy == 0:
                            self.BOT.pump_buy = self.BOT.current_price
                        self.BOT.profit = round((self.BOT.current_price / self.BOT.pump_buy - 1) * 100, 2)

                    if self.BOT.logging:
                        self.BOT.data_to_log.append(data)
                        # self.nprint(self.BOT.history[-1])
                except:
                    PrintException()

            return new_get_markets

        self.API.get_markets = get_markets_decorator(self.API.get_markets)

        def get_balances_decorator(f):
            @exception_handler('get_balances')
            def new_get_balances(self, *args, **kwargs):
                try:
                    result, error = f(*args, **kwargs)
                    if error is None:
                        result = result
                        self.BOT.balances = result
                        self.BOT.balance_last_update_time = time.time()
                    if self.BOT.logging:
                        self.BOT.data_to_log.append(
                            {'time': time.time(), 'type': 'get_balance', 'result': result, 'error': error})
                except:
                    PrintException()

            return new_get_balances

        self.API.get_balance = get_balances_decorator(self.API.get_balance)

        def get_orders_decorator(f):
            @exception_handler('get_orders')
            def new_get_orders(self, *args, **kwargs):
                market = self.BOT.currency + '_BTC'
                result, error = f(market=market)
                self.BOT.orders = result

            return new_get_orders

        self.API.get_orders = get_orders_decorator(self.API.get_orders)

        def submit_trade_decorator(f):
            def new_submit_trade(self, *args, **kwargs):
                if self.BOT.allow_orders:
                    f(*args, **kwargs)
                else:
                    self.BOT.nprint("[!] Training Mode Active. No real orders are being placed.")
                if self.BOT.logging:
                    self.BOT.data_to_log.append(
                        {'time': time.time(), 'type': trade_type, 'result': [market, rate, amount], 'error': ''})

            return new_submit_trade

        self.API.submit_trade = submit_trade_decorator(self.API.submit_trade)

        def ping(self):
            t1 = time.time()
            self.get_currencies()
            t2 = time.time()
            self.BOT.nprint('latency: ', round(t2 - t1, 2))

        self.API.ping = ping

    @exception_handler('force_buy')
    def force_buy(self, coin, btc_value):
        price = self.get_price(coin + '/BTC')['AskPrice'] * (1 + self.pump_buy)
        total_coin_value = ((btc_value - (btc_value * 0.00201)) - 0.0005) / price
        FINAL_BTC_BALANCE = float(self.get_coin_balance('BTC')['Available']) - btc_value
        last_balance_update = 0
        last_market_update = 0
        time_wait = 1 / (2 * min(self.balance_requests_per_second, self.history_requests_per_second))

        # Считается количество возможных спусков
        if self.pump_buy_max == 0 or self.pump_buy == 0:
            niterations = 1
        else:
            niterations = max(round(self.pump_buy_max / self.pump_buy), 1)

        self.nprint('Balance after buying %s: ' % self.currency, self.get_coin_balance(self.currency)['Available'])
        self.nprint('Balance before buying BTC: ', self.get_coin_balance('BTC')['Available'])
        self.nprint('[+] Buying coins...')
        for iteraion in range(niterations):
            if float(self.get_coin_balance('BTC')['Available']) - FINAL_BTC_BALANCE >= self.API.minimal_order_value \
                    and float(self.get_coin_balance(coin)['Available']) <= total_coin_value:
                # Проверка обновилась ли инфа о балансах и рынках
                if (last_balance_update != self.balance_last_update_time and
                            last_market_update != float(self.history[-1]['time'])):
                    time.sleep(0.01)
                    last_balance_update = self.balance_last_update_time
                    last_market_update = float(self.history[-1]['time'])

                    # Выставляется ордер
                    value = float(self.get_coin_balance('BTC')['Available']) - FINAL_BTC_BALANCE
                    price = float(self.get_price(coin + '/BTC')['AskPrice']) * (1 + self.pump_buy)
                    coins = (value - (value * 0.00201)) / price
                    self.nprint('[+] Placing buy order on {:.8f} ({:.2f}%)'.format(price, 100 * price / float(
                        self.get_price(coin + '/BTC')['AskPrice'])))
                    self.nprint('[+] BTC left to spend {:.8f}'.format(
                        float(self.get_coin_balance('BTC')['Available']) - FINAL_BTC_BALANCE))

                    # thread_id = self.add_task(self.API.submit_trade, self.API, coin + '/BTC', 'Buy', price, coins)
                    # self.execute(thread_id)

                    # Пишем цену покупки
                    self.buying_price = price
                    self.API.submit_trade(coin + '/BTC', 'Buy', price, coins)
                    # Ждем исполнения ордера
                    time.sleep(time_wait)
                    time.sleep(0.01)
                    # Отменяем неисполненный ордер
                    self.nprint('[+] Removing buy order.')
                    thread_id = self.add_task(self.API.cancel_trade, 'All')
                    self.execute(thread_id)
                if self.allow_orders is False:
                    break
                # Ждем обновления баланса
                self.wait_with_tk_update(time_wait)
            else:
                break
        self.nprint('Balance after buying %s: ' % self.currency, self.get_coin_balance(self.currency)['Available'])
        self.nprint('Balance after buying BTC: ', self.get_coin_balance('BTC')['Available'])

    @exception_handler('force_sell')
    def force_sell(self, coin=None):
        if coin is None:
            coin = self.currency
        price = self.get_price(coin + '/BTC')['BidPrice'] * (1 - self.pump_sell)
        last_balance_update = 0
        last_market_update = 0
        time_wait = 1 / (2 * min(self.balance_requests_per_second, self.history_requests_per_second))

        # Считается количество возможных сдвигов
        if self.pump_sell_max == 0 or self.pump_sell == 0:
            niterations = 1
        else:
            niterations = max(round(self.pump_sell_max / self.pump_sell), 1)

        self.nprint('Balance after buying %s: ' % self.currency, self.get_coin_balance(self.currency)['Available'])
        self.nprint('Balance before selling BTC: ', self.get_coin_balance('BTC')['Available'])
        self.nprint('[+] Selling coins...')
        for iteraion in range(niterations):
            if float(self.get_coin_balance(coin)['Available']) * price >= self.API.minimal_order_value:
                # Проверка обновилась ли инфа о балансах и рынках
                if (last_balance_update != self.balance_last_update_time and
                            last_market_update != float(self.history[-1]['time'])):
                    time.sleep(0.01)
                    last_balance_update = self.balance_last_update_time
                    last_market_update = float(self.history[-1]['time'])

                    # Выставляется ордер
                    price = float(self.get_price(coin + '/BTC')['AskPrice']) * (1 - self.pump_sell)
                    coins = float(self.get_coin_balance(coin)['Available'])
                    self.nprint('[+] Placing sell order.')
                    self.nprint('[+] Placing sell order on {:.8f} ({:.2f}%)'.format(price, 100 * price / float(
                        self.get_price(coin + '/BTC')['AskPrice'])))
                    self.nprint('[+] Coins left: {:.8f}'.format(coins))

                    thread_id = self.add_task(self.API.submit_trade, self.API, coin + '/BTC', 'Sell', price, coins)
                    self.execute(thread_id)
                    # Ждем исполнения ордера
                    time.sleep(time_wait)
                    # Отменяем неисполненный ордер
                    self.nprint('[+] Moving sell order.')
                    time.sleep(0.01)
                    thread_id = self.add_task(self.API.cancel_trade, 'All')
                    self.execute(thread_id)
                if self.allow_orders is False:
                    break
                # Ждем обновления баланса
                time.sleep(time_wait)
            else:
                break
        self.nprint('Balance after selling %s: ' % self.currency, self.get_coin_balance(self.currency)['Available'])
        self.nprint('Balance after selling BTC: ', self.get_coin_balance('BTC')['Available'])
        self.RUNNING = False

    def get_coin_balance(self, coin):
        for c in self.balances:
            if c['Symbol'] == coin:
                return c

    def get_price(self, pair, i=-1, data=None):

        if data is None:
            data = self.history
        for p in data[i]['market']:
            if p['Label'] == pair:
                return p

    def thread_wrapper(self, f):
        def new_f(*args):
            self.active_threads += 1
            try:
                f(*args)
                self.active_threads -= 1
            except Exception as e:
                self.nprint('Error in thread erase: ', e)
                self.active_threads -= 1

        return copy.deepcopy(new_f)

    def add_task(self, f, *args, name='Thread'):
        f = self.thread_wrapper(f)
        task = threading.Thread(target=f, args=args, name=name)
        self.task_pool.append(task)
        time.sleep(0.01)
        return (len(self.task_pool) - 1)

    @exception_handler('execute')
    def execute(self, thread_id=None):
        if thread_id is None:
            while len(self.task_pool) > 0:
                if self.active_threads < self.threads:
                    thread = self.task_pool[0]
                    del self.task_pool[0]
                    thread.start()
        else:
            thread_id = min(thread_id, len(self.task_pool) - 1)
            thread = self.task_pool[thread_id]
            del self.task_pool[thread_id]
            thread.start()

    @exception_handler('balance_record')
    def balance_record(self):
        while self.RUNNING:
            if self.balance_record_active:
                thread_id = self.add_task(self.API.get_balance, self.API)
                self.execute(thread_id)
                time.sleep(1 / self.balance_requests_per_second)
            else:
                break

    @exception_handler('history_record')
    def history_record(self):
        while True:
            if self.history_record_active and self.RUNNING:
                if len(self.history) < self.history_length:
                    thread_id = self.add_task(self.API.get_markets, self.API, name='GetMarkets')
                    # time.sleep(0.01)
                    self.execute(thread_id)
                else:
                    thread_id = self.add_task(self.API.get_markets, self.API, name='GetMarkets')
                    # time.sleep(0.01))
                    self.execute(thread_id)

                try:
                    self.VIEW.plot()
                except:
                    PrintException()
                self.VIEW.root.update()

                time.sleep(1 / self.history_requests_per_second)
            else:
                break

    def orders_record(self):
        while True:
            if self.orders_record_active and self.RUNNING:
                thread_id = self.add_task(self.API.get_orders, self.API)
                self.execute(thread_id)
                time.sleep(1 / self.orders_requests_per_second)
            else:
                break

    def log(self):
        while self.logging and self.RUNNING:
            if len(self.data_to_log) > 0:
                for i in self.data_to_log:
                    self.log_file_name.write(json.dumps(i) + '\n')
            self.data_to_log = []

            time.sleep(self.log_sleep_time)

    def callback(self, client, update, users, chats, *args, **kwargs):
        non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
        self.callback_called = True

        def parseCoin(s):
            m = re.search(self.REGEXP, s)
            # if m and 'PUMP STARTS'.lower() in s.lower() and 'Cryptopia'.lower() in s.lower():
            if m:
                return m.group(1).strip()
            return ''

        self.pump_start_id = len(self.history) - 1
        currency = ''
        if isinstance(update, str):
            currency = update
        else:
            try:
                update = str(update).translate(non_bmp_map)
                update = json.loads(update)
                if update['_'] == 'types.UpdateNewChannelMessage':
                    if str(update['message']['to_id']['channel_id']) == self.Channel:
                        msg = str(update['message']['message']).translate(non_bmp_map)
                        self.nprint(msg)
                        currency = parseCoin(msg)
                        self.nprint(currency)
            except:
                PrintException()
                self.nprint(update)
                return

        if currency == '':
            return
        self.currency = currency

        # Устанавливаем цену начала пампа
        try:
            self.client.stop()
        except:
            pass
        self.start_price = float(self.get_price(self.currency + '/BTC')['AskPrice'])
        # Получаем глубину рынка
        thread_id = self.add_task(self.API.get_orders, self.API)
        self.execute(thread_id)

        # Делаем покупку
        self.min_price = self.current_price
        for i in self.history:
            price = self.get_price(self.currency + '/BTC', 0, data=[i])['AskPrice']
            if float(price) < self.min_price:
                self.min_price = float(price)

        if self.current_price < self.min_price * self.buy_price_max_point:
            self.force_buy(self.currency, self.PUMP_BALANCE)
        else:
            self.nprint(
                '[!] Buying has been termiated because pump too high already! Current pump size is {:.2f} %'.format(
                    (self.current_price * 100) / self.min_price))

        self.nprint('Buying ended. Trading..')

        # Запускаем функцию анализа
        self.trade(1)

    def trade(self, delay=5):
        while self.RUNNING:
            if len(self.INDICATORS) > 0:
                result = sum(list([i() for i in self.INDICATORS]))
            else:
                result = 0
            self.nprint('Trading...')
            if result > 0:
                break
            self.wait_with_tk_update(1)

        for i in range(len(self.INDICATORS)):
            try:
                del self.INDICATORS[i]
                del self.INDICATORS[i].model
            except:
                pass

        if self.manual_sell is False:
            self.force_sell(self.currency)

    def get_signal(self):
        def update_handler(client, update, users, chats):
            self.nprint(update)

        if self.manual:
            self.nprint('\n***Wait input data***\n')
            PUMP_COIN = input().rstrip(' \t\r\n\0').upper()
            self.callback(update=PUMP_COIN, client=None, users=None, chats=None)
            # self.callback('TEST')
        else:
            self.nprint(self.PHONE)
            self.client = Client(
                session_name="pyro",
                phone_number=self.PHONE,
                phone_code=str(27982)  # input("code: "),
            )

            # client = Client('pyro')

            self.client.set_update_handler(self.callback)
            # client.set_update_handler(update_handler)
            self.client.start()
            self.callback_called = False
            # self.nprint(self.client.get_me().user)
            self.nprint(self.client.get_me())
            # self.client.idle()
            while self.callback_called == False:
                self.wait_with_tk_update(1)

    def nprint(self, *args):
        print(*args)
        text = pprint.pformat(args)
        try:
            self.VIEW.Log.insert(self.VIEW.tk.END, text)
        except:
            PrintException()


if __name__ == '__main__':
    BOT = Bot()
