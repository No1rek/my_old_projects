import time
import json
from clients.extended_clients.extended_clients import BitfinexCli, BinanceCli
from clients.extended_clients.clients_trades import Binance, Bitmex, Bitfinex
from misc.candle_scraper import DataScraper
from misc.binary_search import binarySearch
import concurrent.futures

class SqueezeScraper:
    def __init__(self, tasks = None):
        self.clients = {
            "binance": Binance(),
            "bitmex": Bitmex(),
            "bitfinex": Bitfinex()
        }
        self.tasks = tasks if tasks is not None else self.load_tasks()
        self.exchanges = {
            "binance": BinanceCli,
            "bitfinex": BitfinexCli
        }

    def load_tasks(self, fname = "tasks"):
        with open(fname) as f:
            tasks = json.load(f)
        return tasks

    def find_candle_squeezes(self, task, case_count_to_select = 100, addit_range = 60000, min_time_between_squeezes=600000, group_split_count=1):
        candles = DataScraper().get_dataset(exchange=task["base_unit"]["exchange"], market=task["base_unit"]["market"],
                                            start=task["start"], end=task["end"])
        candles = sorted(candles, key=lambda x: x[2]/x[3])

        candle_groups = []
        for i in range(0, len(candles), int(len(candles)/group_split_count)):
            candle_groups.append(candles[i:i + int(len(candles)/group_split_count)])
        candles = []
        for g in candle_groups:
            print(len(g))
            candles += g[:case_count_to_select]
        candles = sorted(candles, key=lambda x: x[2] / x[3])


        top_candles = []
        unavailable_timings = []
        for i in range(len(candles)-1, -1, -1):
            if len(top_candles) == 0:
                top_candles.append(candles[i])
                unavailable_timings.append(candles[i][0])
            else:
                closest = binarySearch(unavailable_timings, candles[i][0])
                if abs(unavailable_timings[closest] - candles[i][0]) > min_time_between_squeezes:
                    top_candles.append(candles[i])
                    unavailable_timings.append(candles[i][0])
            if len(top_candles) == case_count_to_select*group_split_count:
                break

        candles = top_candles
        cases = [[c[0]-addit_range, c[0]+addit_range] for c in candles]
        return cases

    def get_trades_for_exchange(self, args):
        unit, start, end = args
        exchange = unit["exchange"]
        market = unit["market"]
        client = self.clients[exchange]
        trades = client.get_trades_for_period(symbol=market, start_time=start, end_time=end)
        self.case[f"{exchange}_{market}"] = (client.get_price_dataset(trades))

    def get_trades_for_case(self, units, start, end):
        self.case = {}
        args = [[unit, start, end] for unit in units]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for _ in executor.map(self.get_trades_for_exchange, args):
                pass

        return self.case

    def save_case_timings(self, tasks_with_cases):
            with open("tasks_with_cases", 'w') as outfile:
                json.dump(tasks_with_cases, outfile)





