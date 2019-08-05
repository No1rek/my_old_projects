import pandas as pd
import json, requests, datetime

report = pd.read_excel('report.xlsx')

profit_trades, average_profit, loss_trades, average_loss = 0,0,0,0

pairs = {}

def get_timestamp(date):
    day = int(date[8:10])
    month = int(date[5:7])
    hours = int(date[11:13])
    minutes = int(date[14:16])
    year = int(date[0:4])
    return datetime.datetime(year, month, day, hours, minutes, 0, 0).timestamp()

def count_positions(report, balance):
    DAY = datetime.datetime(2019, 2, 20, 0).timestamp()

    for index, row in report.iterrows():
        if row[1] not in pairs.keys() and row[2] == 'SELL' and (get_timestamp(row[0]) >= DAY): ###################3
            pairs[row[1]] = {'sell': 0, 'buy':0, 'closed':False, 'last_opening_time':100, 'position_count':0}
            pairs[row[1]]['sell'] += float(row[5])
        else:
            if row[2] == 'SELL' and row[1] in pairs.keys():
                if (get_timestamp(row[0]) >= DAY or pairs[row[1]]['sell']/max(pairs[row[1]]['buy'], 0.0000001)-1 > 0.2):
                    pairs[row[1]]['sell'] += float(row[5])


            if row[2] == 'SELL' and get_timestamp(row[0]) < DAY and row[1] in pairs.keys() \
                    and  abs(pairs[row[1]]['sell']/max(pairs[row[1]]['buy'], 0.0000001)-1) < 0.2:
                pairs[row[1]]['closed'] = True

                continue
            if row[1] in pairs.keys():
                if row[2] == 'BUY' and pairs[row[1]]['closed'] == False:
                    if abs(pairs[row[1]]['last_opening_time'] - get_timestamp(row[0])) > 1800:
                        pairs[row[1]]['position_count'] += 1

                    pairs[row[1]]['buy'] += float(row[5])
                    pairs[row[1]]['last_opening_time'] = get_timestamp(row[0])

    profits, profits_vol, losses, losses_vol = [], [], [], []

    trades_from_balance = add_current_balance_as_trades(balance)

    for pair in pairs.keys():
        if pair[:-3] in trades_from_balance.keys() and pair in ['LRCETH']:
            pairs[pair]['sell'] += trades_from_balance[pair[:-3]]

    print(pairs)
    for pair, result in pairs.items():

        if result['sell'] == 0 or result['buy'] == 0 or abs(result['sell']/result['buy']-1) > 0.5:
            if result['buy'] == 0:
                print(f"Ignored pair {pair} with 0 positions")
                continue
            print(f"Ignored pair {pair} ")
            continue
        if result['sell'] > result['buy']:
            profits.append((result['sell'] / result['buy'] - 1)*result['sell'])
            profits_vol.append(result['sell'])
        if result['sell'] < result['buy']:
            losses.append((result['sell'] / result['buy'] - 1)*result['sell'])
            losses_vol.append(result['sell'])

        print(f"{pair} {result['position_count']} {result['sell']/result['buy'] - 1} {result['buy']}")

    profit_trades = len(profits)
    loss_trades = len(losses)
    average_profit = sum(profits)/sum(profits_vol) if len(profits) > 0 else 0
    average_loss = sum(losses) / sum(losses_vol) if len(losses) > 0 else 0

    print(f"PROFIT {average_profit} {profit_trades} LOSS {average_loss} {loss_trades} TOTAL SELL {sum(losses_vol+profits_vol)}")

BALANCE = {
    'MFT': 75965,
    'TRX': 47582,
    'POE': 25935,
    'AION': 1914.75,

    'ETH': 103.1092569,
    'BNB': 9.24905655,
}

def add_current_balance_as_trades(balance):
    ticker = json.loads(requests.get("https://api.binance.com/api/v3/ticker/price").content)
    ticker = {t['symbol']: float(t['price']) for t in ticker}
    ticker["ETHETH"] = 1.0
    trades = {}
    for symbol in balance.keys():
        if not symbol in ['ETH', 'BNB']:
            trades[symbol] = balance[symbol] * ticker[symbol+'ETH']

    return trades


def evaluate_balance(balance):
    ticker = json.loads(requests.get("https://api.binance.com/api/v3/ticker/price").content)
    ticker = {t['symbol']:float(t['price']) for t in ticker}
    ticker["ETHETH"] = 1.0
    BALANCE = 0
    for symbol in balance.keys():
        BALANCE += balance[symbol] * ticker[symbol+'ETH']

    print(f"BALANCE: {BALANCE}")


if __name__ == "__main__":
    count_positions(report, BALANCE)
    evaluate_balance(BALANCE)