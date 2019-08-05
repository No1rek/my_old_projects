import requests
import re
import json
import math



class WalletCollector:
    def __init__(self):
        self.base_url = "https://bitinfocharts.com/ru/top-100-richest-bitcoin-addresses-%s.html"
        self.transactions_api_url = "https://api.blockchain.info/charts/balance?address=%s&timespan=1year&format=json"
        self.wallets = []

    def get_wallets(self, frompage=1, topage=500, save=False):
        for p in range(frompage, topage+1, 1):
            print(f"Getting wallets from page {p}")
            page = requests.get(self.base_url%str(p)).content.decode('utf-8')
            wallets = self.parse_page(page)

            wallets = [self.get_wallet_transactions(w) for w in wallets]

            self.wallets = self.wallets + wallets



        if save is True:
            self.save_wallets(self.wallets)

    def parse_page(self, page):
        return re.findall(r">([a-zA-Z0-9^<>\s]{34})<", page)

    def save_wallets(self, wallets):
        with open("wallets.txt", "w") as f:
            f.write(json.dumps(wallets))

    def load_wallets(self):
        with open("wallets.txt", "r") as f:
            wallets = json.load(f)
        return wallets

    def get_wallet_transactions(self, wallet):
        print(f"getting transactions for wallet {wallet}")
        data = json.loads(requests.get(self.transactions_api_url%wallet).content)
        x, y = [], []
        for v in data["values"]:
            x.append(v["x"])
            y.append(v["y"])
        wallet = {"w":wallet, "x":x, "y":y}
        return wallet

    def load_prices(self):
        with open("prices.json", "r") as f:
            candles = json.load(f)
        return {str(c[0]):c[4] for c in candles}


    def rate_wallets(self, wallets, prices, min_transaction = 0.15, min_positions=0):
        length = len(wallets)
        for j in range(length):
            w = wallets[j]
            print(f"{round(j/length*100,2)}% completed of {length} wallets =======================================")
            x, y = w["x"], w["y"]
            result = 1
            pos_open, pos_close, max_vol, min_vol = 0, 0, -math.inf, math.inf
            if len(x) < 3:
                w["r"] = result
                continue

            max_vol = max(y)
            min_vol = min(y)
            max_range = max_vol - min_vol
            positions = 0

            for i in range(len(x)):
                if i > 0:
                    timestamp = str(round(x[i] * 1000 / 14400000) * 14400000)
                    if timestamp in prices.keys():
                        if (y[i] - y[i-1])/max_range > min_transaction and pos_open == 0:
                            pos_open = prices[timestamp]
                        elif (y[i] - y[i-1])/max_range < -1*min_transaction and pos_open != 0:
                            pos_close = prices[str(round(x[i] * 1000 / 14400000) * 14400000)]
                            positions += 1
                            result = result * pos_close/pos_open
                            pos_open, pos_close = 0, 0
            if positions < min_positions:
                w["r"] = result
                continue
            w["r"] = result
        return sorted(wallets, key=lambda x:x["r"])

    def top(self, wallets, n=10):
        antitop = list(wallets[:n])
        top = list(wallets[-n:])
        top = [{"w":t["w"], "r":t["r"]} for t in top]
        antitop = [{"w": t["w"], "r": t["r"]} for t in antitop]
        return {"top":top, "antitop":antitop}


if __name__ == "__main__":
    wc = WalletCollector()
    prices = wc.load_prices()
    # wc.get_wallets(frompage=1, topage=100, save=True)
    wallets = wc.load_wallets()
    wallets = wc.rate_wallets(wallets=wallets, prices=prices, min_transaction=0.2, min_positions=4)
    print(wc.top(wallets=wallets, n=30))