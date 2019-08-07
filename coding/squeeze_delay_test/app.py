import json
from clients.extended_clients.clients_trades import Binance, Bitmex
from plotter import Plotter


def execute(start, end, units):
    clients = {
        "binance": Binance(),
        "bitmex": Bitmex()
    }
    data = {}
    for unit in units:
        exchange = unit["exchange"]
        market = unit["market"]
        client = clients[exchange]
        trades = client.get_trades_for_period(symbol=market, start_time=start, end_time=end)
        data[f"{exchange}_{market}"] = (client.get_price_dataset(trades))
    Plotter().plot(data)


def run():
    with open("tasks") as f:
        tasks = json.load(f)
    for task in tasks:
        start = task["start"]
        end = task["end"]
        units = task["units"]
        name = f""
        execute(start=start, end=end, units=units)


if __name__ == "__main__":
    run()