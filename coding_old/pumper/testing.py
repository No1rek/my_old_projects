from cryptopia_api import Api
import numpy as np
import random
import time
from data_processing import *
import matplotlib.pyplot as plt
from keras.models import load_model


class TestApi(Api):
    def __init__(self, KEY, SECRET, BOT):
        super(TestApi, self).__init__(KEY, SECRET)
        self.BOT = BOT
        self.number_of_trades = 1000
        self.pump_duration = 180
        self.initial_price = 0.000336
        self.pump_percentage_raise = 185

        self.DP = DataProcessing()
        self.DATA = self.DP.generate_parabol_new(self.number_of_trades, random.randint(10, 60) / 100,
                                                 random.randint(3, 10) / 100,
                                                 -0.4, 0.5, 0.1, cut=False)

        self.DATA['x'] = np.array(self.DATA['x']) * self.pump_duration + time.time()
        self.DATA['y'] = np.array(self.DATA['y']) * self.initial_price * (
        self.pump_percentage_raise - 100) / 100 + self.initial_price

        self.DATA['balance'] = [
            {
                "Symbol": "BTC",
                "Available": "0.50000000",
            },
            {
                "Symbol": "TEST",
                "Available": "0.00000000",
            }
        ]

        self.data = list([
            {'time': self.DATA['x'][i], 'price': self.DATA['y'][i], 'balance': self.DATA['balance'], 'active': True}
            for i in range(len(self.DATA['x']))])

        self.BOT.currency = 'TEST'

    def cancel_trade(self, feature_requested):
        return None

    def get_orders(self, market):
        return {'Buy':[], 'Sell':[]}

    def api_query(self, feature_requested=None):
        t = time.time()
        if t < self.data[0]['time']:
            return self.data[0]
        for i in range(len(self.data[:-1])):
            if self.data[i]['time'] <= t and self.data[i + 1]['time'] > t:
                return self.data[i]
        return self.data[-1]

    def get_balance(self, currency=''):
        result = self.api_query()['balance']
        return result, None

    def get_markets(self):
        price = self.api_query()['price']
        result = [{
            "Label": "TEST/BTC",
            "AskPrice": price,
            "BidPrice": price - (random.randint(0,5) * price)/100,
        }]
        return result

    def submit_trade(self, market, trade_type, rate, amount):
        t = time.time()
        try:
            if trade_type == 'Sell':
                for i in range(len(self.data)):
                    try:
                        next_elem = self.data[i + i]
                    except:
                        next_elem = self.data[-1]
                    if self.data[i]['price'] >= rate and self.data[i]['time'] <= t and next_elem['time'] > t:
                        new_balance = [
                            {
                                "Symbol": "BTC",
                                "Available": str(float(self.data[i]['balance'][0]["Available"]) + rate * amount),
                            },
                            {
                                "Symbol": "TEST",
                                "Available": float(self.data[i]['balance'][1]["Available"]) - amount,
                            }
                        ]
                        for d in self.data[i:]:
                            d['balance'] = new_balance
                            d['active'] = False
                        break

            if trade_type == 'Buy':
                for i in range(len(self.data)):
                    try:
                        next_elem = self.data[i + i]
                    except:
                        next_elem = self.data[-1]
                    if self.data[i]['price'] <= rate and self.data[i]['time'] <= t and next_elem['time'] > t:
                        new_balance = [
                            {
                                "Symbol": "BTC",
                                "Available": str(float(self.data[i]['balance'][0]["Available"]) - rate * amount),
                            },
                            {
                                "Symbol": "TEST",
                                "Available": float(self.data[i]['balance'][1]["Available"]) + amount,
                            }
                        ]
                        for d in self.data[i:]:
                            d['balance'] = new_balance
                        break
        except Exception as e:
            print('Exception in test buy/sell: ', e)
        return '[!] Coins bought', None
