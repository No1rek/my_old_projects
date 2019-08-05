from clients.utils.templates import *
from clients.utils.auth import GetAPIKeys
from clients.utils.api_decorators import log_cls_methods
from ccxt.base.exchange import Exchange
from clients.utils.api_decorators import async_measure_latency
from clients.utils.api_decorators import rate_limiter


class BaseAsyncClient(Exchange):
    __metaclass__ = log_cls_methods
    # нужно еще добавить функционал для перевода тикеров и рынков с сокетов в такой же вид, как с REST
    def __init__(self, API_KEY=None, API_SECRET=None):
        API_KEY, API_SECRET = GetAPIKeys()

        self.API_KEY, self.API_SECRET = API_KEY, API_SECRET

        if self.API_KEY and self.API_SECRET:
            self.apiKey, self.secret = self.API_KEY, self.API_SECRET

        self.load_markets()

    def set_ratelimits(self, ratelimits, default=2000):
        if 'default' in ratelimits.keys():
            default = ratelimits['default']
            del ratelimits['default']

        for f in ratelimits.keys():
            if hasattr(self, f):
                if ratelimits[f] > 0:
                    setattr(self, f, rate_limiter(self, ratelimits[f])(getattr(self, f)))
                else:
                    setattr(self, f, rate_limiter(self, default)(getattr(self, f)))

    
    def _translate(self, msg_type, msg=None):
        exchange = self.Exchange

        try:
            if msg_type == 'order_book':
                translator = WS_ORDERBOOK_TRANSLATOR[exchange]
            elif msg_type == 'ticker' or msg_type == 'tickers':
                translator = WS_TICKER_TRANSLATOR[exchange]
            elif msg_type == 'balance':
                translator = WS_BALANCE_TRANSLATOR[exchange]
            elif msg_type == 'candles':
                translator = WS_CANDLES_TRANSLATOR[exchange]
        except:
            assert ("Translation error. No dictionary for {0} exchange!".format(exchange))

        if msg:
            result = {}
            for k, v in translator.items():
                if v != '':
                    try:
                        result[k] = msg[v]
                    except:
                        pass
                else:
                    result[k] = ''
            return result
        else:
            return translator

    # REST methods

    @async_measure_latency
    async def async_get_symbols(self):
        await self.load_markets()

        return self.currencies

    @async_measure_latency
    async def async_check_limits(self):
        raise NotImplementedError()

    @async_measure_latency
    async def async_get_exchange_info(self):  # todo: must to be standartizated
        return await self.describe()

    @async_measure_latency
    async def async_get_market_info(self):
        return await self.load_markets()

    @async_measure_latency
    async def async_check_server_time(self):
        return await self.get_server_time()['serverTime']

    @async_measure_latency
    async def async_account_info(self):
        raise NotImplementedError()

    @async_measure_latency
    async def async_buy(self, symbol, amount, price):
        if isinstance(amount, float) or isinstance(amount, int):
            amount = float(amount)
            amount = "{0:.8f}".format(amount)
        if isinstance(price, float) or isinstance(price, int):
            price = float(price)
            price = "{0:.8f}".format(price)
        return await self.create_limit_buy_order(symbol, amount, price)

    @async_measure_latency
    async def async_check_order(self, id, symbol, **kwargs):
        return await self.fetch_order(id, symbol, kwargs)

    @async_measure_latency
    async def async_sell(self, symbol, amount, price):
        if isinstance(amount, float) or isinstance(amount, int):
            amount = float(amount)
            amount = "{0:.8f}".format(amount)
        if isinstance(price, float) or isinstance(price, int):
            price = float(price)
            price = "{0:.8f}".format(price)
        return await self.create_limit_sell_order(symbol, amount, price)

    @async_measure_latency
    async def async_buy_limit(self):
        raise NotImplementedError()

    @async_measure_latency
    async def async_sell_limit(self):
        raise NotImplementedError()

    @async_measure_latency
    async def async_cancel(self, id, symbol, **kwargs):
        return await self.cancel_order(id, symbol, params=kwargs)

    @async_measure_latency
    async def async_get_order_book(self, symbol, length=None, **kwargs):
        return await self.fetch_order_book(symbol, length, **kwargs)

    @async_measure_latency
    async def async_get_active_orders(self, symbol=None, since=None, limit=None, params={}, *args, **kwargs):
        return await self.fetch_open_orders(symbol, since, limit, params, *args, **kwargs)

    @async_measure_latency
    async def async_get_orders(self, symbol=None, since=None, limit=None, params={}, *args, **kwargs):
        return await self.fetch_open_orders(symbol, since, limit, params, *args, **kwargs)

    @async_measure_latency
    async def async_get_open_orders(self, symbol=None, since=None, limit=None, **kwargs):
        return await self.fetch_open_orders(symbol, since, limit, params=kwargs)

    @async_measure_latency
    async def async_get_closed_orders(self, symbol=None, since=None, limit=None, **kwargs):
        return await self.fetch_closed_orders(symbol, since, limit, params=kwargs)

    @async_measure_latency
    async def async_balance(self, **kwargs):
        return await self.fetch_balance(**kwargs)

    @async_measure_latency
    async def async_get_trades(self, symbol, **kwargs):
        return await self.fetch_trades(symbol, params=kwargs)

    @async_measure_latency
    async def async_get_ticker(self, symbol):
        return await self.fetch_ticker(symbol)

    @async_measure_latency
    async def async_get_all_tickers(self, **kwargs):
        if self.has['fetch_tickers']:
            return await self.fetch_tickers(**kwargs)
        else:
            raise Exception("Exchange doesn't support such function: %s" % 'fetch_tickers')  # PUT THIS IN DECORATOR

    @async_measure_latency
    async def async_get_ohlcv(self, symbol, period, **kwargs):
        if self.has['fetch_ohlcv']:
            return await self.fetch_ohlcv(symbol, period, **kwargs)
        else:
            raise Exception("Exchange doesn't support such function: %s" % 'get_ohlcv')




class WSSBaseClient:
    __metaclass__ = log_cls_methods
    def __init__(self, manager, *args, **kwargs):
        self.Manager = manager
        self.API_KEY = self.Manager.API_KEY
        self.API_SECRET = self.Manager.API_SECRET

        self.ws_client = None

    def _ws_callback_wrapper(self, callback, msg_type):
        parse_function = {
            'order_book': self._ws_parse_order_book,
            'balance': self._ws_parse_balance,
            'ticker': self._ws_parse_ticker,
            'tickers': self._ws_parse_tickers,
            'candles': self._ws_parse_candles,
        }[msg_type]

        def new_callback(msg):
            msg = parse_function(msg)
            return callback(msg)

        return new_callback

    def _pair_ex_to_comm(self, symbol):
        return symbol

    def _pair_comm_to_ex(self, symbol):
        return symbol

    def currency_comm_to_ex(self, currency):
        if not self.Manager.markets:
            self.Manager.load_markets()
        else:
            return self.Manager.currencies[currency]['id']

    def currency_ex_to_comm(self, currency):
        if not self.Manager.markets:
            self.Manager.load_markets()
        else:
            for k,v in self.Manager.currencies.items():
                if v['id'] == currency:
                    return k

    # Standartizing WSS outputs

    def _ws_parse_order_book(self, msg):
        return self.Manager._translate('order_book', msg)

    def _ws_parse_ticker(self, msg):
        return self.Manager._translate('ticker', msg)

    def _ws_parse_tickers(self, msg):
        return self.Manager._translate('ticker', msg)

    def _ws_parse_balance(self, msg):
        return self.Manager._translate('balance', msg)

    def _ws_parse_candles(self, msg):
        return self.Manager._translate('candles', msg)
