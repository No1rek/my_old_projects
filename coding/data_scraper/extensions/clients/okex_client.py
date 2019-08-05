from clients.client_base import BaseClient
from clients.client_base_async import BaseAsyncClient
from clients.client_base import WSSBaseClient
import json
from threading import Thread

import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time

from ccxt.okex import okex

import websocket

class OkexClient(BaseAsyncClient, BaseClient, okex):

    QUOTE_CURRENCIES = ['USDT', 'BTC', 'ETH', 'OKB']
    RateLimits = {
        "default": 0,
        "get_symbols": 0,
        "check_limits": 0,
        "get_exchange_info": 0,
        "get_market_info": 0,
        "check_server_time": 0,
        "account_info": 0,
        "buy": 0,
        "check_order": 0,
        "sell": 0,
        "buy_limit": 0,
        "sell_limit": 0,
        "cancel": 0,
        "get_order_book": 0,
        "get_active_orders": 0,
        "get_orders": 0,
        "get_open_orders": 0,
        "get_closed_orders": 0,
        "balance": 0,
        "get_trades": 0,
        "get_ticker": 0,
        "get_all_tickers": 0,
        "get_ohlcv": 0
    }

    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True,*args, **kwargs):
        self.Exchange = 'bitfinex'
        okex.__init__(self, {'apiKey':API_KEY, 'secret':API_SECRET})
        BaseAsyncClient.__init__(self, )
        BaseClient.__init__(self, )
        self.ws_client = WSSOkexClient(self, self.API_KEY, self.API_SECRET)
        if rateLimiting is True:
            self.set_ratelimits(self.RateLimits)


class WSSOkexClient(WSSBaseClient):
    def __init__(self, manager, *args, **kwargs):
        WSSBaseClient.__init__(self, manager, *args, **kwargs)
        websocket.enableTrace(True)

    def depth_error(self, ws, error):
        print("Error in depth websocket! ", str(error))

    def depth_close(self, ws):
        print("Depth socket has been closed!")

    def stop(self):
        # Will stop all websockets when they will be implemented
        self.stop_depth_ws()

    def stop_depth_ws(self):
        if hasattr(self, 'depth_ws'):
            if not self.depth_ws is None:
                self.depth_ws.alive = False

    def subscribe_to_depth(self, ws):
        ws.send("{'event':'addChannel','channel':'ok_sub_spot_%s_depth'}" % self.ws_depth_symbol)
        ws.alive = True


    def _ws_format_pair(self, symbol):
        symbol = symbol.split('/')
        return "_".join(symbol)

    def start_depth_socket(self, callback, symbol):
        self.ws_depth_symbol = self._ws_format_pair(symbol)
        self.depth_ws = websocket.WebSocketApp("wss://real.okex.com:10441/websocket",
                                         on_message=callback,
                                         on_error=self.depth_error,
                                         on_close=self.depth_close,
                                         on_open=self.subscribe_to_depth)

        t = Thread(target=self.depth_ws.run_forever)
        t.start()

    def ws_loop_order_book(self, callback, symbol):
        symbol = self._pair_comm_to_ex(symbol)
        callback = self._ws_callback_wrapper(callback, 'order_book')
        self.start_depth_socket(symbol=symbol, callback=callback)

    def _pair_comm_to_ex(self, symbol):
        market_pair_list = [self.Manager.markets[m]['id'] for m in self.Manager.markets.keys()]
        if symbol in market_pair_list:
            return symbol
        symbol = symbol.split('/')
        symbol[0], symbol[1] = self.currency_comm_to_ex(symbol[0]), self.currency_comm_to_ex(symbol[1])
        symbol = "/".join(symbol)
        return symbol

    def _ws_parse_order_book(self, msg):
        # Requires implementation
        res = msg[1:-1]
        res =json.loads(res)["data"]
        res["asks"] = [[float(a[0]), float(a[1])] for a in res["asks"]]
        res["bids"] = [[float(a[0]), float(a[1])] for a in res["bids"]]
        return res