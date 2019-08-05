import time, threading, signal

from ccxt.bitfinex import bitfinex
from clients.client_base import BaseClient
from clients.client_base_async import BaseAsyncClient
from clients.client_base import WSSBaseClient

from btfxwss import BtfxWss as btfxwss
from btfxwss.queue_processor import QueueProcessor
from btfxwss.connection import WebSocketConnection


class BitfinexClient(BaseAsyncClient, BaseClient, bitfinex):

    QUOTE_CURRENCIES = ['USD', 'BTC', 'ETH', 'EUR', 'JPY', 'GBP', 'EOS']
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

    def __init__(self, API_KEY='', API_SECRET='', rateLimiting=True, *args, **kwargs):
        self.Exchange = 'bitfinex'
        bitfinex.__init__(self, {'apiKey':API_KEY, 'secret':API_SECRET})
        BaseAsyncClient.__init__(self, )
        BaseClient.__init__(self, )
        self.ws_client = WSSBitfinexClient(self, self.API_KEY, self.API_SECRET)
        if rateLimiting is True:
            self.set_ratelimits(self.RateLimits)





class WSSBitfinexClient(WSSBaseClient):
    def __init__(self, manager, *args, **kwargs):
        WSSBaseClient.__init__(self, manager, *args, **kwargs)
        self.ws = btfxwss_new(key=self.API_KEY, secret=self.API_SECRET)

    def ws_loop_order_book(self, callback, symbol):
        symbol = self._pair_comm_to_ex(symbol)
        callback = self._ws_callback_wrapper(callback, 'order_book')
        if self.ws.alive is False:
            self.ws.start()
            while not self.ws.conn.connected.is_set():
                time.sleep(1)
        self.ws.subscribe_to_order_book(symbol)
        self.ws.queue_processor.book_callback = callback

    def _ws_parse_order_book(self, msg):
        res = {'asks':[], 'bids':[]}
        if not type(msg[0][0][0]) is list:
            msg[0][0] = [msg[0][0]]
        res['asks'] = [[m[0], m[2]] for m in msg[0][0] if m[2] < 0 and m[0] != 0]
        res['bids'] = [[m[0], m[2]] for m in msg[0][0] if m[2] > 0 and m[0] != 0]
        res['timestamp'] = msg[1]
        return res

    def _ws_parse_ticker(self, msg):
        ts = msg[1]
        data = msg[0][0]
        msg = {"ts": ts}

        for i in range(len(data)):
            msg[str(i)] = data[i]

        result = self.Manager._translate('tickers', msg)
        result['symbol'] = self.ws_client._pair_ex_to_comm(result['symbol'])
        return result

    def _ws_parse_candles(self, msg):
        ts = msg[1]
        try:
            # For first message
            _ = msg[0][0][0][0]
            msg = msg[0][0]
        except:
            # For another ones
            msg = msg[0]
        msg = sorted(msg, key=lambda x: x[0])
        data = msg[-1]

        msg = {}
        for i in range(len(data)):
            msg[str(i)] = data[i]
        msg["0"] = ts

        result = self.Manager._translate('candles', msg)
        return result


    def ws_loop_ticker(self, callback, symbol):
        symbol = self._pair_comm_to_ex(symbol)
        callback = self._ws_callback_wrapper(callback, 'ticker')
        if self.ws.alive is False:
            self.ws.start()
            while not self.ws.conn.connected.is_set():
                time.sleep(1)
        self.ws.subscribe_to_ticker(symbol)
        self.ws.queue_processor.ticker_callback = callback

    def ws_loop_candles(self, callback, symbol):
        symbol = self._pair_comm_to_ex(symbol)
        callback = self._ws_callback_wrapper(callback, 'candles')
        if self.ws.alive is False:
            self.ws.start()
            while not self.ws.conn.connected.is_set():
                time.sleep(1)
        self.ws.subscribe_to_candles(symbol)
        self.ws.queue_processor.candles_callback = callback


    def _pair_ex_to_comm(self, symbol):
        symbol = [symbol[:-3], symbol[-3:]]
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


class btfxwss_new(btfxwss):
    def __init__(self, key=None, secret=None, log_level=None, **wss_kwargs):
        btfxwss.__init__(self, key, secret, log_level)
        self.key = key if key else ''
        self.secret = secret if secret else ''
        self.alive = False
        try:
            self.conn = WebSocketConnection(log_level=log_level,
                                            **wss_kwargs)
        except:
            self.conn.reconnect()
        self.queue_processor = QueueProcessor_new(self.conn.q,
                                                  log_level=log_level)

        self._alive = True
        self.keep_alive_interval = 1

        self.T = threading.Thread(target=self.keep_alive)


    def keep_alive(self, interval=0.1):
        keepalive = True
        while keepalive:
            keepalive = self._alive
            time.sleep(interval)
        self.stop()


    def start(self):
        """Start the client.

        :return:
        """
        self._alive = True
        self.T.start()

        self.conn.start()
        self.queue_processor.start()

    def stop(self, *args):
        """Stop the client.

        :return:
        """
        self._alive = False
        self.conn.disconnect()
        self.queue_processor.join()

class QueueProcessor_new(QueueProcessor):
    def __init__(self, *args, **kwargs):
        QueueProcessor.__init__(self, *args, **kwargs)

        self.ticker_callback = None
        self.book_callback = None
        self.trades_callback = None
        self.candles_callback = None
        self.raw_book_callback = None

    def _handle_ticker(self, dtype, data, ts):
        self.log.debug("_handle_ticker: %s - %s - %s", dtype, data, ts)
        channel_id, *data = data
        channel_identifier = self.channel_directory[channel_id]
        entry = (data, ts)
        self.ticker_callback(entry)
        self.tickers[channel_identifier].put(entry)

    def _handle_book(self, dtype, data, ts):
        self.log.debug("_handle_book: %s - %s - %s", dtype, data, ts)
        channel_id, *data = data
        self.log.debug("ts: %s\tchan_id: %s\tdata: %s", ts, channel_id, data)
        channel_identifier = self.channel_directory[channel_id]
        entry = (data, ts)
        self.book_callback(entry)
        self.books[channel_identifier].put(entry)

    def _handle_raw_book(self, dtype, data, ts):
        self.log.debug("_handle_raw_book: %s - %s - %s", dtype, data, ts)
        channel_id, *data = data
        channel_identifier = self.channel_directory[channel_id]
        entry = (data, ts)
        self.raw_book_callback(entry)
        self.raw_books[channel_identifier].put(entry)

    def _handle_trades(self, dtype, data, ts):
        self.log.debug("_handle_trades: %s - %s - %s", dtype, data, ts)
        channel_id, *data = data
        channel_identifier = self.channel_directory[channel_id]
        entry = (data, ts)
        self.trades_callback(entry)
        self.trades[channel_identifier].put(entry)

    def _handle_candles(self, dtype, data, ts):
        self.log.debug("_handle_candles: %s - %s - %s", dtype, data, ts)
        channel_id, *data = data
        channel_identifier = self.channel_directory[channel_id]
        entry = (data, ts)
        self.candles_callback(entry)
        self.candles[channel_identifier].put(entry)
