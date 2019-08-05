from clients.client_base import BaseClient
from clients.client_base_async import BaseAsyncClient
from clients.client_base import WSSBaseClient


from ccxt.binance import binance

from binance.client import Client
from binance.websockets import BinanceSocketManager


class BinanceClient(BaseAsyncClient, BaseClient, binance):

    QUOTE_CURRENCIES = ['BNB', 'BTC', 'ETH', 'USDT']
    RateLimits = {
        "default" : 250,
        "get_symbols" : 0,
        "check_limits" : 0,
        "get_exchange_info" : 0,
        "get_market_info" : 0,
        "check_server_time" : 0,
        "account_info" : 0,
        "buy" : 0,
        "check_order" : 0,
        "sell" : 0,
        "buy_limit" : 0,
        "sell_limit" : 0,
        "cancel" : 0,
        "get_order_book" : 0,
        "get_active_orders" : 0,
        "get_orders" : 0,
        "get_open_orders" : 0,
        "get_closed_orders" : 0,
        "balance" : 0,
        "get_trades" : 0,
        "get_ticker" : 0,
        "get_all_tickers" : 0,
        "get_ohlcv" : 0
    }

    def __init__(self, API_KEY=None, API_SECRET=None, rateLimiting=True,  *args, **kwargs):
        self.Exchange = 'binance'
        binance.__init__(self, {'apiKey': API_KEY, 'secret': API_SECRET})
        BaseAsyncClient.__init__(self, )
        BaseClient.__init__(self, )
        self.ws_client = WSSBinanceClient(self)
        if rateLimiting is True:
            self.set_ratelimits(self.RateLimits)


class WSSBinanceClient(WSSBaseClient):
    def __init__(self, manager, *args, **kwargs):
        WSSBaseClient.__init__(self, manager, *args, **kwargs)
        self.binance_api = Client(self.API_KEY, self.API_SECRET) #
        self.ws = BinanceSocketManager(self.binance_api)

    def ws_loop_order_book(self, callback, symbol):
        symbol = self._pair_comm_to_ex(symbol)
        callback = self._ws_callback_wrapper(callback, 'order_book')
        self.ws.start_depth_socket(symbol=symbol, callback=callback)
        self.ws.start()


    def ws_loop_tickers(self, callback):
        callback = self._ws_callback_wrapper(callback, 'tickers')
        self._ws_tickers_connection_key = self.ws.start_ticker_socket(callback=callback)
        self.ws.start()

    def _pair_ex_to_comm(self, symbol):
        for s in self.Manager.QUOTE_CURRENCIES:
            if (symbol.find(s) == len(symbol) - len(s)):
                symbol = symbol[0:symbol.find(s)]
                sym = [symbol, s]
                symbol = sym
                break
        # symbol = symbol.split("/")
        symbol[0], symbol[1] = self.currency_ex_to_comm(symbol[0]), self.currency_ex_to_comm(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def _pair_comm_to_ex(self, symbol):
        market_pair_list = [self.Manager.markets[m]['id'] for m in self.Manager.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.currency_comm_to_ex(symbol[0]), self.currency_comm_to_ex(symbol[1])
        symbol = "".join(symbol)
        return symbol

    def _ws_parse_order_book(self, msg):
        msg = self.Manager._translate('order_book', msg)
        temp = []
        for a in msg['asks']:
            temp.append([a[0], a[1]])

        msg['asks'] = temp
        temp = []

        for b in msg['bids']:
            temp.append([b[0], b[1]])

        msg['bids'] = temp
        return msg

    def _ws_parse_tickers(self, msg):
        result = []
        for symbol in msg:
            res = self.Manager._translate('tickers', symbol)
            res['symbol'] = self.ws_client._pair_ex_to_comm(res['symbol'])
            result.append(res)
        return result
