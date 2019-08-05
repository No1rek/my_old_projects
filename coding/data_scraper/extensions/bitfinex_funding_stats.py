import datetime
import requests
import time
import json


def extend(url="", **params):
    url += "?"
    for k, v in params.items():
        if v is not None:
            url += f"{k}={v}&"
    return url

def get_positions(market, type, start, end):
    url = extend(f"https://api2.bitfinex.com:3000/api/v2/stats1/pos.size:1m:t{market}:{type}/hist", **dict(start=start, end=end))
    return json.loads(requests.get(url).content)


def get_funding_stats(market, type, start, end, sleep_interval=0):
    curr_start, total_result, curr_end = None, [], round(
        datetime.datetime.now().timestamp() * 1000) if end is None else int(end)

    while curr_start is None or curr_end > int(start):
        result = get_positions(market=market, type=type, start=start, end=end)
        time.sleep(sleep_interval)
        total_result = total_result + result

        time_difference = len(result) * 60000

        if len(result) == 0:
            break

        if curr_start is None:
            curr_start = curr_end
            curr_end -= time_difference
            curr_start -= (time_difference + min(time_difference, curr_end - int(start)))
        else:
            curr_end -= time_difference
            curr_start -= min(time_difference, curr_end - int(start))

    sorted_result = sorted(total_result, key=(lambda x: x[0]))
    # cutting redundant candles
    result = []
    for candle in sorted_result:
        if candle[0] >= start and candle[0] <= end:
            result.append(candle)
    return result

if __name__ == "__main__":
    res = get_funding_stats("BTCUSD", type="short", start=1546009200000, end=1546011000000)
    print(res)