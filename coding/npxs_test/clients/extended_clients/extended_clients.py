from clients.binance_client import BinanceClient
from clients.bitfinex_client import BitfinexClient
from clients.okex_client import OkexClient
from clients.hitbtc_client import HitbtcClient
import requests
from datetime import datetime
# from add_volumes import count_zeros


import time

def count_zeros(number):
    number = format(float(number), '.10f')
    ret = 0
    if number[0] != '0':
        return 0
    point_passed = False
    for i in number:
        if i == "." or i==",":
            point_passed = True
            continue
        if point_passed is True and i != '0':
            return ret
        if point_passed is True and i == '0':
            ret += 1
    return ret


class BinanceCli(BinanceClient):
    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True, *args, **kwargs):
        BinanceClient.__init__(self, API_KEY, API_SECRET, rateLimiting, *args, **kwargs)

    def get_candle_history(self, **kwargs):
        params = {'interval':kwargs.get('interval')}
        if kwargs.get('start'):
            params['startTime'] = str(round(int(kwargs.get('start'))))
        if kwargs.get('end'):
            params['endTime'] = str(round(int(kwargs.get('end'))))

        res = self.fetch_ohlcv(symbol=kwargs.get('symbol'), params=params, limit=1000)  #'endTime': kwargs.get('end')
        return res, {}

    def symbol_to_coinmarket_format(self, symbol):
        market_pair_list = [self.markets[m]['id'] for m in self.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.ws_client.currency_comm_to_ex(symbol[0]), self.ws_client.currency_comm_to_ex(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def get_precision_and_volumes(self):
        markets = self.publicGetTicker24hr()
        markets = {m['symbol']:m for m in markets}
        result = {}
        for m, data in markets.items():
            try:
                quote = [qc for qc in self.QUOTE_CURRENCIES if qc in data['symbol'] and data['symbol'].find(qc) + len(qc) == len(data['symbol'])][0]
                if quote == 'USDT':
                    volume = float(data['quoteVolume'])/float(markets['BTCUSDT']['weightedAvgPrice'])
                elif quote == 'BTC':
                    volume = float(data['quoteVolume'])
                else:
                    volume = float(data['quoteVolume'])*float(markets[quote+'BTC']['weightedAvgPrice'])

                zeros = count_zeros(data['weightedAvgPrice'])
                if m == "NPXSBTC":
                    zeros = count_zeros(data['weightedAvgPrice'])
                result[self.ws_client._pair_ex_to_comm(m)] = {'zeros': zeros, 'volume': volume}
            except Exception as e:
                result[self.ws_client._pair_ex_to_comm(m)] = {'zeros':-1, 'volume':-1}
        return result



class BitfinexCli(BitfinexClient):
    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True, *args, **kwargs):
        BitfinexClient.__init__(self, API_KEY, API_SECRET, rateLimiting, *args, **kwargs)

    def get_candle_history(self, unit, **kwargs):
        while True:
            try:
                params = {'interval':kwargs.get('interval'), 'sort':-1,}
                if kwargs.get('end') and kwargs.get('start'):
                     limit= round(min(1000, (kwargs.get('end') - kwargs.get('start')) / (60 * 1000)))
                else:
                    limit = 1000

                if kwargs.get('end'):
                    params['end'] = str(round(int(kwargs.get('end'))))
                if kwargs.get('limit'):
                    limit = round(int(kwargs.get('limit')))
                res = self.fetch_ohlcv(symbol=kwargs.get('symbol'),timeframe=kwargs.get('interval'), limit=limit, params=params)[::-1]
                return res, {}
            except:
                time.sleep(90)
    def symbol_to_coinmarket_format(self, symbol):
        market_pair_list = [self.markets[m]['id'] for m in self.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.ws_client.currency_comm_to_ex(symbol[0]), self.ws_client.currency_comm_to_ex(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def get_precision_and_volumes(self):
        markets = self.publicGetTickers()
        # markets = map(lambda x: x['pair'] = , markets) [dict(**{'pair':self.symbol_to_coinmarket_format(m['pair'])}, **m) for m in markets]
        markets = {m['pair']:m for m in markets}
        result = {}
        for m, data in markets.items():
            try:
                quote = [qc for qc in self.QUOTE_CURRENCIES if qc in data['pair'] and data['pair'].find(qc) + len(qc) == len(data['pair'])][0]
                if quote == 'USD':
                    volume = (float(data['volume'])*float(data['mid']))/float(markets['BTCUSD']['mid'])
                elif quote == 'BTC':
                    volume = float(data['volume'])*float(data['mid'])
                else:
                    volume = float(data['volume'])*float(data['mid'])*float(markets[quote+'BTC']['mid'])

                zeros = count_zeros(data['volume'])
                result[self.ws_client._pair_ex_to_comm(m)] = {'zeros': zeros, 'volume': volume}
            except Exception as e:
                result[self.ws_client._pair_ex_to_comm(m)] = {'zeros':-1, 'volume':-1}
        return result


class OkexCli(OkexClient):
    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True, *args, **kwargs):
        OkexClient.__init__(self, API_KEY, API_SECRET, rateLimiting, *args, **kwargs)

    def get_candle_history(self, unit, **kwargs):
        # self.options["warnOnFetchOHLCVLimitArgument"] = False
        while True:
            try:
                params = {'interval':kwargs.get('interval')}
                if kwargs.get('end') and kwargs.get('start'):
                    limit = round(min(1000, (kwargs.get('end') - kwargs.get('start')) / (60 * 1000)))
                else:
                    limit = 1000                # Но тут может быть и 2000
                if kwargs.get('start'):
                    since = kwargs.get('start')
                else:
                    since = kwargs.get('end') - limit*60*1000
                res = self.fetch_ohlcv(symbol=kwargs.get('symbol'), limit=None, since=since, params=params)
                return res[:limit], {}
            except Exception as e:
                time.sleep(300)
    def symbol_to_coinmarket_format(self, symbol):
        market_pair_list = [self.markets[m]['id'] for m in self.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.ws_client.currency_comm_to_ex(symbol[0]), self.ws_client.currency_comm_to_ex(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def get_precision_and_volumes(self):
        markets = self.publicGetTickers()['tickers']
        markets = {m['symbol']:m for m in markets}
        result = {}
        for m, data in markets.items():
            try:
                quote = [qc for qc in self.QUOTE_CURRENCIES if qc in data['symbol'] and data['symbol'].find(qc) + len(qc) == len(data['pair'])][0]
                if quote == 'USD':
                    volume = float(data['volume'])/float(markets['BTCUSD']['mid'])
                elif quote == 'BTC':
                    volume = float(data['volume'])
                else:
                    volume = float(data['volume'])*float(markets[quote+'BTC']['mid'])

                zeros = count_zeros(data['volume'])
                result[m] = {'zeros': zeros, 'volume': volume}
            except Exception as e:
                result[m] = {'zeros':-1, 'volume':-1}
        return result


class HitbtcCli(HitbtcClient):
    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True, *args, **kwargs):
        HitbtcClient.__init__(self, API_KEY, API_SECRET, rateLimiting, *args, **kwargs)

    def get_candle_history(self, unit, **kwargs):
        while True:
            try:
                limit = 1000
                res = self.modified_fetch_ohlcv(kwargs.get('symbol'))
                return res[:limit], {'make_break':True}
            except Exception as e:
                time.sleep(120)

    def symbol_to_coinmarket_format(self, symbol):
        market_pair_list = [self.markets[m]['id'] for m in self.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.ws_client.currency_comm_to_ex(symbol[0]), self.ws_client.currency_comm_to_ex(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def reformat_candles(self, candles):
        res = []
        for c in candles:
            ts = int(datetime.strptime(c['timestamp'], "%Y-%m-%dT%H:%M:%S.000Z").timestamp()*1000)
            res.append([ts, float(c['open']), float(c['max']), float(c['min']), float(c['close']), float(c['volume'])])
        return res



    def modified_fetch_ohlcv(self, symbol, since=None, limit=1000, params={}):
        import json
        symbol = self.ws_client._pair_comm_to_ex(symbol)
        try:
            data = json.loads(requests.get(f"https://api.hitbtc.com/api/2/public/candles/{symbol}?period=M1&limit={limit}").content)
            data = self.reformat_candles(data)
        except:
            data = []
        return data

if __name__ == "__main__":
    pass
    # bc = OkexCli()
    # bc.get_precision_and_volumes()
    # import datetime
    # from datetime import datetime, timezone
    # start = datetime.strptime("01.01.2018", "%d.%m.%Y").replace(
    #     tzinfo=timezone.utc).timestamp()

    # bn = BitfinexCli()
    # a = bn.get_precision_and_volumes()
    # A = 5

    # start = round(time.time()*1000-60000000)
    # bn = BinanceCli().get_candle_history(unit=None, symbol="ETH/BTC", start=start, interval='1m')[0]
    # print(bn[-1][0])
    # print(len(bn))
    # hc = HitbtcCli().get_candle_history(unit=None, symbol="ETH/BTC", start=start, interval='1m')[0]
    # print(hc[-1][0])
    # print(len(hc))
    # bf = BitfinexCli().get_candle_history(unit=None, symbol="ETH/BTC", start=start, interval='1m')[0]
    # print(bf[-1][0])
    # print(len(bf))
    # ok = OkexCli().get_candle_history(unit=None, symbol="ETH/BTC", start=start, interval='1m')[0]
    # print(ok[-1][0])
    # print(len(ok))


    # import datetime
    # from datetime import datetime, timezone
    # start = datetime.strptime("01.01.2018", "%d.%m.%Y").replace(
    #     tzinfo=timezone.utc).timestamp()
    # start2 = datetime.strptime("02.01.2018", "%d.%m.%Y").replace(
    #     tzinfo=timezone.utc).timestamp()
    # print(HitbtcCli(API_KEY='dad5d603b3696a939ba505d3931bf677', API_SECRET='28eeb57d11775fd40add3c9f29897274').get_candle_history(unit=None, symbol="ETH/BTC", start=start))
    # print(HitbtcCli().get_candle_history(unit=None, symbol="ETH/BTC", start=start2))

