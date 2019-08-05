import pandas as pd
import json, requests

report = pd.read_excel('report.xlsx')

# {'last_opening_time':0, 'buy':0, 'sell':0, 'count':0, 'volume':0}

pairs = {}

def get_hours(date):
    return float(date[11:13])



for index, row in report.iterrows():
    if row[1] not in pairs.keys():
        pairs[row[1]] = {'last_opening_time':0, 'buy':0, 'sell':0, 'count':0}
        if row[2] == 'SELL':
            pairs[row[1]]['sell'] += float(row[5])
        else:
            pairs[row[1]]['buy'] += float(row[5])
            pairs[row[1]]['last_opening_time'] = get_hours(row[0])

    else:
        if row[2] == 'SELL':
            pairs[row[1]]['sell'] += float(row[5])
        else:
            pairs[row[1]]['buy'] += float(row[5])

            if abs(get_hours(row[0]) - pairs[row[1]]['last_opening_time']) > 0:
                  pairs[row[1]]['count'] += 1

            pairs[row[1]]['last_opening_time'] = get_hours(row[0])




for pair in pairs.keys():
    if pairs[pair]['buy'] > 0:
        print(f"{pair} {pairs[pair]['count']} {pairs[pair]['sell']/pairs[pair]['buy'] - 1} {pairs[pair]['buy']}")