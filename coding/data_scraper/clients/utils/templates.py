
#############################################################################################
############## DICTIONARIES USED TO COMPARE AND TRANSLATE FIELDS ############################
#############################################################################################

WS_ORDERBOOK_TRANSLATOR = {
    'binance':
        {
            'bids': 'b',
            'asks': 'a',
            'timestamp': 'u',
            'symbol': 's'
        },
    'bitfinex':
        {
            'bids':'bids',
            'asks':'asks',
            'timestamp': 'lastUpdateId',
            'symbol':'',
        },

}



WS_TICKER_TRANSLATOR = {
    'binance':
        {
            'symbol':        "s",
            'info':          "",                       #"{ the original non-modified unparsed reply from exchange API },
            'timestamp':     "E",
            'datetime':      "",                       #ISO8601 datetime string with milliseconds
            'high':          "h",
            'low':           "l",
            'bid':           "b",
            'bidVolume':     "B",
            'ask':           "a",
            'askVolume':     "A",
            'vwap':          "",                           #float, // volume weighed average price
            'open':          "o",
            'close':         "c",
            'last':          "c",
            'previousClose': "x",
            'change':        "",                               # float, // absolute change, `last - open`
            'percentage':    "",                                #float, // relative change, `(change/open) * 100`
            'average':       "",                                #float, // average price, `(last + open) / 2`
            'baseVolume':    "v",
            'quoteVolume':   "q"
        },
    'bitfinex':
        {
            'symbol': "",
            'info': "",  # "{ the original non-modified unparsed reply from exchange API },
            'timestamp': "ts",
            'datetime': "",  # ISO8601 datetime string with milliseconds
            'high': "8",
            'low': "9",
            'bid': "0",
            'bidVolume': "1",
            'ask': "2",
            'askVolume': "3",
            'vwap': "",  # float, // volume weighed average price
            'open': "",
            'close': "6",
            'last': "6",
            'previousClose': "",
            'change': "4",  # float, // absolute change, `last - open`
            'percentage': "5",  # float, // relative change, `(change/open) * 100`
            'average': "",  # float, // average price, `(last + open) / 2`
            'baseVolume': "7",
            'quoteVolume': "",
        }
}

WS_BALANCE_TRANSLATOR = {
    'binance':
        {
            'info': '',
            'free': '',
            'used': '',
            'total': ''
        }
}

WS_CANDLES_TRANSLATOR = {
    'bitfinex':
        {
            'timestamp': '0',
            'open': '1',
            'high': '3',
            'low': '4',
            'close': '2',
            'volume': '5',
        }
}


