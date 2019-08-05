import json
import requests

import time
import datetime

class BaseClient:
    def extend(self, url="", **params):
        url += "?"
        for k,v in params.items():
            if v is not None:
                url+=f"{k}={v}&"
        return url



class Binance(BaseClient):
    def __init__(self, delay=0.1):
        self.api_url = "https://api.binance.com"

    def get_historical_trades(self, symbol, limit=1000, startTime=None, endTime=None, fromId=None):
        url = self.api_url + "/api/v1/aggTrades"
        response = json.loads(requests.get(self.extend(url=url,
                                                       symbol=symbol,
                                                       limit=limit,
                                                       startTime=startTime,
                                                       endTime=endTime,
                                                       fromId=fromId)).content)
        return response

    def get_trades_for_period(self, symbol, start_time, end_time=time.time()*1000, collect_trades=True):
        trades = []
        batch = self.get_historical_trades(symbol=symbol, startTime=start_time-60*60*1000, endTime=start_time)
        if len(batch) > 0:
            next_trade = batch[-1]
        else:
            return trades

        while len(batch) > 0 and next_trade['T'] < end_time:
            try:
                batch = self.get_historical_trades(symbol=symbol, fromId=next_trade['a'])
                if len(batch) > 0:
                    next_trade = batch[-1]
                    del batch[-1]
                else:
                    return trades

                if collect_trades is True:
                    trades += batch
            except:
                pass
        if collect_trades is True:
            trades += [next_trade]

        ret = []
        for t in trades:
            if t["T"] <= end_time:
                 ret.append(t)
        return ret

    def get_price_dataset(self, trades):
        x, y = [], []
        for t in trades:
            x.append(t["T"])
            y.append(t["p"])
        return {"x": x, "y": y}


class Bitmex(BaseClient):
    def __init__(self, delay=0.1):
        self.api_url = "https://www.bitmex.com/api/v1"

    def get_historical_trades(self, symbol, limit=500, startTime=None, endTime=None, start=0):
        url = self.api_url + "/trade"
        if startTime is not None:
            startTime = str(datetime.datetime.fromtimestamp(startTime/1000).strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        if endTime is not None:
            endTime = str(datetime.datetime.fromtimestamp(endTime/1000).strftime("%Y-%m-%dT%H:%M:%S.000Z"))

        response = json.loads(requests.get(self.extend(url=url,
                                                       symbol=symbol,
                                                       count=limit,
                                                       startTime=startTime,
                                                       endTime=endTime,
                                                       start=start)).content)
        return response

    def get_trades_for_period(self, symbol, start_time, end_time=time.time()*1000, tz=2, ids_check_lim=300, max_repeats = 2):
        start_time -= tz*3600000
        end_time -= tz*3600000
        start = start_time
        trades = []
        ids = []

        new_trades = 0
        last_time_to_make_offset, offset, repeats, last_time = "", 0, 0, 0
        while True:
            try:
                batch = self.get_historical_trades(symbol=symbol, startTime=start_time, endTime=end_time, start=offset)
                for t in batch:
                    trade_time = datetime.datetime.strptime(t["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()*1000
                    if last_time_to_make_offset != t["timestamp"]:
                        last_time_to_make_offset = t["timestamp"]
                        offset = 0
                    else:
                        offset += 1



                    if t["trdMatchID"] not in ids\
                            and trade_time >= start\
                            and trade_time >= start_time\
                            and trade_time <= end_time:
                        if len(ids) < ids_check_lim:
                            ids.append(t["trdMatchID"])
                        else:
                            del ids[0]
                            ids.append(t["trdMatchID"])

                        trades.append(t)
                        new_trades += 1

                if len(batch) == 0:
                    offset = 0



                new_trades = 0
                last_time = start_time


                if new_trades == 0:
                    if start_time + 1000 < end_time:

                        start_time = max(datetime.datetime.strptime(trades[-1]["timestamp"],
                                                            "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000 + 1000,
                                         start_time + 1000)
                    else:
                        print("No new trades")
                        break
                else:
                    start_time = datetime.datetime.strptime(trades[-1]["timestamp"],
                                                            "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000

                if last_time == start_time:
                    repeats += 1
                else:
                    repeats = 0

                if repeats >= max_repeats:
                    repeats = 0
                    start_time += 1000

                print(f"[{datetime.datetime.now()}] Progress  {(start_time - start)/(end_time-start)*100:.2f}% current time: {datetime.datetime.fromtimestamp(start_time/1000)} end time: {datetime.datetime.fromtimestamp(end_time/1000)}, unique trades: {len(trades)}" )
            except Exception as e:
                print("Bitmex sleeping")
                time.sleep(120)
        ret = []
        for t in trades:
            t["timestamp"] = datetime.datetime.strptime(t["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()+3600*tz
            if  (t["timestamp"]-3600*tz)*1000 < end_time:
                ret.append(t)
        return ret

    def get_price_dataset(self, trades):
        x, y = [], []
        for t in trades:
            x.append(t["timestamp"]*1000)
            y.append(t["price"])
        return {"x":x, "y":y}


class Bitfinex(BaseClient):
    def __init__(self, delay=0.1):
        self.api_url = "https://api.bitfinex.com/v2"

    def get_trades_for_period(self, symbol, start_time, end_time=time.time() * 1000, collect_trades=True, tz=0):
        start_time += tz * 3600000
        end_time += tz * 3600000
        trades = []
        last_batch_ids = []
        while True:
            try:

                batch = json.loads(requests.get(f"https://api.bitfinex.com/v2/trades/t{symbol}/hist?end={end_time}&limit=1000").content)
                new_trades = []
                for t in batch:
                    if t[0] not in last_batch_ids and t[1] >= start_time:
                        new_trades.append(t)
                        last_batch_ids.append(t[0])

                if len(new_trades) == 0:
                    break

                end_time = sorted(new_trades, key=lambda x: x[1])[0][1]
                trades += new_trades
            except:
                print("Bitfinex error")
                time.sleep(45)
        ret = []
        for t in trades:
            t[1] -= tz*3600000
            ret.append(t)
        return sorted(ret, key=lambda x: x[1])


    def get_price_dataset(self, trades):
        x, y = [], []
        for t in trades:
            x.append(t[1])
            y.append(t[3])
        return {"x": x, "y": y}



if __name__ == "__main__":
    start = 1544781655000
    end = 1544781840000
    print(Bitfinex().get_trades_for_period("BTCUSD", start_time=start, end_time=end)) #[0][1]/1000
    print(Binance().get_trades_for_period("BTCUSDT", start_time=start, end_time=end)[0]['T']/1000)
    print(Bitmex().get_trades_for_period("XBTUSD", start_time=start, end_time=end)[0]['timestamp'])