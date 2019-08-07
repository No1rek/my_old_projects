from decimal import Decimal
from clients.extended_clients.clients_trades import Binance
from scraper import DataScraper
import json
import numpy as np
import time


def get_cases(trades,volume=50, precision=Decimal("0.00000001"), dangerous_period = -1, from_time = 0):
    trades = [{'T':Decimal(t['T']), 'p':Decimal(t['p']), 'q':Decimal(t['q'])} for t in trades if float(t['T']) > from_time]
    ask = trades[0]["p"]
    bid = ask - precision
    cases = []
    for i in range(len(trades)):
        trade = trades[i]
        if trade["p"] > ask:
            ask = trade["p"]
            bid = ask - precision
        if trade["p"] < bid:
            bid = trade["p"]
            ask = bid + precision
            j = i - 1
            cum_volume = 0
            t1,t2 = 0,trades[j]["T"]
            while j > 0:
                if trades[j]["p"] == ask:
                    cum_volume += trades[j]["p"] * trades[j]["q"]
                if trades[j]["p"] > ask + precision or trades[j]["p"] == bid:
                    break
                if cum_volume >= volume:
                    t1 = trades[j]["T"]
                    if float(t2-t1)/1000 < dangerous_period or dangerous_period < 0:
                        cases.append({"t1":float(t1)/1000.0, "t2": float(t2)/1000.0, 'bid': float(bid), 'ask':float(ask)})
                    break
                j -= 1
    return cases

def check_influence_factors(market, cases, btc_change_periods = None, btc_periods_to_compare = 12,
                            currency_volatility_change_periods = None, curr_volat_periods_to_compare = 6):
    if btc_change_periods is None:
        btc_change_periods = ["15m", "30m", "1h", "12h"] # ["15m", "30m", "1h", "4h", "6h", "12h", "1d"]
    if currency_volatility_change_periods is None:
        currency_volatility_change_periods = ["1h", "6h", "1d"] # ["1h", "6h", "1d"]


    ret = {
        'btc_price_change': {p: {'avg': [], 'last': [], 'diff': []} for p in btc_change_periods},
        'btc_volume_change': {v: {'avg': [], 'last': [], 'diff': []} for v in btc_change_periods},
        'curr_volatility_change': {v: {'avg': [], 'last': [], 'diff': []} for v in currency_volatility_change_periods},
    }


    scraper = DataScraper()


    for i in range(len(cases)):
        try:
            last_time = time.time()
            case = cases[i]

            last_1m_candle = int(case['t1']/60 - 1)*60000
            last_btc_price = scraper.get_dataset(exchange='binance', market='BTC/USDT', start=last_1m_candle, end=last_1m_candle+120000)[0][1]
            for period in ret['btc_price_change'].keys():
                period_time = scraper.intervals['binance'][period]
                period_start_time = (int(case['t1']*1000/period_time) - btc_periods_to_compare)*period_time
                period_end_time = int(case['t1']*1000 / period_time + 1) * period_time
                candles = scraper.get_dataset(exchange='binance', market='BTC/USDT', start=period_start_time, end=period_end_time, interval=period)
                candles = [c for c in candles if c[0] >= period_start_time and c[0] <= period_end_time]

                average_price_changes = np.average(np.array([abs(1 - candles[i][1]/candles[i - 1][1]) for i in range(1, len(candles) - 1)]))
                ret['btc_price_change'][period]['avg'].append(average_price_changes)
                ret['btc_price_change'][period]['last'].append(abs(1 - last_btc_price/candles[-1][1]))
                # ret['btc_price_change'][period]['diff'].append(abs(1 - last_btc_price/candles[-1][1])/ \
                #                                                average_price_changes)

                average_volume =  np.average(np.array([candles[i][5] for i in range(0, len(candles) - 1)]))
                ret['btc_volume_change'][period]['avg'].append(average_volume)
                ret['btc_volume_change'][period]['last'].append(candles[-1][5])
                # ret['btc_volume_change'][period]['diff'].append(candles[-1][5] / \
                #                                                 average_volume)

            for period in ret['curr_volatility_change'].keys():
                period_time = scraper.intervals['binance'][period]
                period_start_time = int(case['t1']*1000 / period_time - curr_volat_periods_to_compare) * period_time
                period_end_time = int(case['t1']*1000 / period_time + 1) * period_time
                candles = scraper.get_dataset(exchange='binance', market=market, start=period_start_time,
                                              end=period_end_time, interval=period)
                candles = [c for c in candles if c[0] >= period_start_time and c[0] <= period_end_time]

                average_volatility = np.average(np.array([candles[i][2]/candles[i][3] for i in range(0, len(candles) - 1)]))
                ret['curr_volatility_change'][period]['avg'].append(average_volatility)
                ret['curr_volatility_change'][period]['last'].append(candles[-1][2]/candles[-1][3])
                # ret['curr_volatility_change'][period]['diff'].append((candles[-1][2] / candles[-1][3])/average_volatility)

        except Exception:
            continue

        progress = i/len(cases)
        print(f"Progress {round(progress*100,4)}%, time left: {round((1 - progress)*(time.time()-last_time),2)} seconds")

    for period in ret['btc_price_change'].keys():
        ret['btc_price_change'][period]['avg_std'] = np.std(ret['btc_price_change'][period]['avg'])
        ret['btc_price_change'][period]['last_std'] = np.std(ret['btc_price_change'][period]['last'])
        ret['btc_price_change'][period]['avg'] = np.average(ret['btc_price_change'][period]['avg'])
        ret['btc_price_change'][period]['last'] = np.average(ret['btc_price_change'][period]['last'])
        # ret['btc_price_change'][period]['diff'] = np.average(ret['btc_price_change'][period]['diff'])

        ret['btc_volume_change'][period]['avg_std'] = np.std(ret['btc_volume_change'][period]['avg'])
        ret['btc_volume_change'][period]['last_std'] = np.std(ret['btc_volume_change'][period]['last'])
        ret['btc_volume_change'][period]['avg'] = np.average(ret['btc_volume_change'][period]['avg'])
        ret['btc_volume_change'][period]['last'] = np.average(ret['btc_volume_change'][period]['last'])
        # ret['btc_volume_change'][period]['diff'] = np.average(ret['btc_volume_change'][period]['diff'])


    for period in ret['curr_volatility_change'].keys():
        ret['curr_volatility_change'][period]['avg_std'] = np.std(ret['curr_volatility_change'][period]['avg'])
        ret['curr_volatility_change'][period]['last_std'] = np.std(ret['curr_volatility_change'][period]['last'])
        ret['curr_volatility_change'][period]['avg'] = np.average(ret['curr_volatility_change'][period]['avg'])
        ret['curr_volatility_change'][period]['last'] = np.average(ret['curr_volatility_change'][period]['last'])
        # ret['curr_volatility_change'][period]['diff'] = np.average(ret['curr_volatility_change'][period]['diff'])


    return ret


def dangerous_cases_to_common(cases, dangerous_period=10 ):
    common, dangerous = 0,0
    for case in cases:
        if case["t2"] - case["t1"] <= dangerous_period:
            dangerous += 1
        else:
            common += 1

    if common ==  0:
        return {"rel":0, "common":0, "dangerous":0, "total":0+0}
    return {"rel":dangerous/common, "common":common, "dangerous":dangerous, "total":common+dangerous}

def get_maximal_price_change_speed(trades, precision=Decimal("0.00000001"), from_time = 0):
    trades = [{'T':Decimal(t['T']), 'p':Decimal(t['p']), 'q':Decimal(t['q'])} for t in trades if float(t['T']) > from_time]
    ask = trades[0]["p"]
    bid = ask - precision
    total_bid_trades_volume = 0
    cases = []
    for i in range(len(trades)):
        trade = trades[i]
        if trade["p"] > ask:
            ask = trade["p"]
            bid = ask - precision
        if trade["p"] < bid:
            bid = trade["p"]
            ask = bid + precision
        if trade["p"] == bid:
            total_bid_trades_volume += float(trades[i]["p"] * trades[i]["q"])

    period = float(trades[-1]['T'] - trades[0]['T'])/1000
    return {'total_bid_trades_volume': total_bid_trades_volume,
            'period': period,
            'speed': total_bid_trades_volume/period}




def save_trades(start, end, market="NPXSBTC"):
    trades = Binance().get_trades_for_period(symbol=market, start_time=start, end_time=end)
    with open(market, 'w') as f:
        json.dump(trades, f)

def load_trades(fname='trades'):
    with open(fname) as f:
        trades = json.load(f)
    return trades

def split_by_periods(trades, interval):
    group_start_time = float(trades[0]['T'])
    group_end_time = group_start_time + interval
    groups = []
    groups.append([trades[0]])
    for t in trades[1:]:
        if t['T'] >= group_start_time and t['T'] < group_end_time:
            groups[-1].append(t)
        else:
            groups.append([])
            groups[-1].append(t)
            group_start_time = float(t['T'])
            group_end_time = group_start_time + interval

    return groups




def statisctical_eval(cases):
    data = [c['t2'] - c['t1'] for c in cases]
    data = np.array(data)
    average = np.average(data)
    std = np.std(data)
    variation = std/average
    min = np.amin(data)
    max = np.amax(data)
    count = len(data)
    return {
        "average": average,
        "std": std,
        "variation": variation,
        "min": min,
        "max": max,
        "count": count,
        "data": data
    }