from clients.extended_clients.clients_trades import Bitmex
import itertools
import json
import datetime
import requests
import os

def update_proxy():
    print(requests.get("https://api.ipify.org?format=json").content)
    proxy = json.loads(requests.get("http://pubproxy.com/api/proxy").content)['data'][0]
    # proxy = {"ipPort":"188.166.211.154:80","ip":"188.166.211.154","port":"80","country":"KR","last_checked":"2019-01-03 10:11:44","proxy_level":"elite","type":"http","speed":"1","support":{"https":0,"get":1,"post":1,"cookies":1,"referer":None,"user_agent":1,"google":0}}
    proxy = f"{proxy['type']}://:@{proxy['ipPort']}"
    print(proxy)
    print(requests.get("https://api.ipify.org?format=json").content)
    os.environ["https_proxy"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    os.environ["http_proxy"] = proxy
    os.environ["HTTP_PROXY"] = proxy
    # print(requests.get("https://google.com").content[:150])
    print(requests.get("https://api.ipify.org?format=json").content)

def check_proxy():
    try:
        requests.get("https://google.com")
        return True
    except:
        return False


def create_splitted_task_file(start, end, interval, market, thresholds, time_intervals):
    # status queued executing finished
    intervals = [{"start":s, "end":s+interval-1, "status":"queued"} for s in range(start, end-interval+1, interval)]
    if end - intervals[-1]["start"] - 1 > 0 :
        intervals.append({"start":intervals[-1]["start"], "end":end, "status":"queued"})

    tasks = {"meta": {"market":market, "thresholds":thresholds, "time_intervals":time_intervals}, "intervals":intervals}

    with open("tasks.txt", 'w') as f:
        json.dump(tasks, f)

    return tasks

def merge_trades():
    trades =[]

    file_list = ["trades1538352002465.0_1538956795887.0.txt",
        "trades1538956802666.0_1539561598376.0.txt",
        "trades1539561603834.0_1539606047978.0.txt",
        "trades1540166404790.0_1540756832920.0.txt",
        "trades1540771203570.0_1541375998537.0.txt",
        "trades1541376003251.0_1541473232955.0.txt",
        "trades1541980804592.0_1542585597234.0.txt",
        "trades1542585602967.0_1542664854747.0.txt",
        "trades1543190407218.0_1543253439923.0.txt",
        "trades1543795205236.0_1544399998267.0.txt",
        "trades1544400004431.0_1545004796712.0.txt",
        "trades1545004803246.0_1545609597627.0.txt",
        "trades1545609603383.0_1546214398168.0.txt",
        "trades1545609603383.0_1546300799386.0.txt"
        ]

    for fname in file_list:
        print(fname)
        with open(f'bitmex_preventer_cases/{fname}', 'r') as f:
            data = json.load(f)

        trades += data

    trades = sorted(trades, key=lambda x: x['x'])

    with open(f'bitmex_preventer_cases/trades', 'w') as f:
        json.dump(trades, f)


def calculate_cases_for_given_trade_batches():
    with open("tasks.txt", 'r') as f:
        tasks = json.load(f)

    task_id = 0
    for task in tasks:
        if task["status"] == "queued":
            task_to_execute = task
            task["status"] = "executing"
            break
        task_id += 1

    with open("tasks.txt", 'w') as f:
        json.dump(tasks, f)

    if task_id < len(tasks):
        tasks[task_id]["status"] = "finished"



    filename = task_to_execute["file"]

    print(filename)
    with open(f'bitmex_preventer_cases/{filename}', 'r') as f:
        trades = json.load(f)

        cases, trades = get_preventer_cases(None, None, None,
                                            [0.003, 0.005, 0.01, 0.0125, 0.015, 0.02],
                                            [5000, 15000, 30000, 45000, 60000], trades=trades)

        with open("result.txt", 'r') as f:
            result = json.load(f)

        for k,v in cases.items():
            if k in result.keys():
                result[k] += v
            else:
                result[k] = v

        with open("result.txt", 'w') as f:
            json.dump(result, f)

    if task_id < len(tasks):
        with open("tasks.txt", 'w') as f:
            json.dump(tasks, f)

            return task_id
    else:
        return None



def select_and_execute_task():
    task_to_execute = None
    with open("tasks.txt", 'r') as f:
        tasks = json.load(f)

    for task in tasks["intervals"]:
        if task["status"] == "queued":
            task_to_execute = task
            task["status"] = "executing"
            break


    with open("tasks.txt", 'w') as f:
        json.dump(tasks, f)

    try:
        with open('bitmex_preventer_cases/data.txt', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    print(f"Pair {[tasks['meta']['market'], task_to_execute['start'], task_to_execute['end']]}")

    cases, trades = get_preventer_cases( tasks["meta"]["market"], task_to_execute["start"], task_to_execute["end"],
                                tasks["meta"]["thresholds"], tasks["meta"]["time_intervals"])
    data[f"{task_to_execute['start']:.8f}_{task_to_execute['end']:.8f}"] = cases


    with open('bitmex_preventer_cases/data.txt', 'w') as f:
        json.dump(data, f)

    with open(f"bitmex_preventer_cases/trades{trades[0]['x']}_{trades[-1]['x']}.txt", 'w') as f:
        json.dump(trades, f)


def get_preventer_cases(symbol, start, end, thresholds, time_intervals, trades=None):
    thresholds, time_intervals = sorted(thresholds), sorted(time_intervals)
    # abc = list(itertools.product(thresholds, time_intervals))
    config_matrix = {f"{c[0]:.8f}_{c[1]:.8f}":[] for c in  list(itertools.product(thresholds, time_intervals))}
    previous_cases_matrix = {f"{c[0]:.8f}_{c[1]:.8f}":0 for c in  list(itertools.product(thresholds, time_intervals))}
    if trades is None:
        trades = Bitmex().get_trades_for_period(symbol=symbol, start_time=start, end_time=end)

        formatted_trades = []
        for t in trades:
            formatted_trades.append({"x":t["timestamp"]*1000, "y":t["price"]})
        trades = formatted_trades

    if len(trades) > 0:
        print(f"Trades have been collected start:{datetime.datetime.fromtimestamp(trades[0]['x']/1000)} end:{datetime.datetime.fromtimestamp(trades[-1]['x']/1000)}")
        print("Finding preventer cases...")

    for t in range(1, len(trades)):
        print(f"[{datetime.datetime.now()}] Progress {t/len(trades)*100:.2f}%")
        i = t - 1
        trade = trades[t]
        min_time = trade['x'] - time_intervals[-1]
        while i >= 0 and trades[i]['x'] >= min_time:
            prev_trade = trades[i]
            brk = False
            time_to_trade = trade['x']  - prev_trade['x']
            price_change = trade['y']/prev_trade['y']  - 1
            way = "up" if price_change > 0 else "down"
            price_change = abs(price_change)

            for threshold_iter in range(len(thresholds)-1, -1, -1):
                for interv_iter in range(len(time_intervals)):
                    if price_change >= thresholds[threshold_iter] and time_to_trade <= time_intervals[interv_iter] \
                        and trade['x'] >= previous_cases_matrix[f"{thresholds[threshold_iter]:.8f}_{time_intervals[interv_iter]:.8f}"] + time_intervals[-1]:
                        timestamp = prev_trade["x"]
                        change = price_change
                        way = way
                        duration = time_to_trade
                        data = [timestamp,  change, way, duration]
                        config_matrix[f"{thresholds[threshold_iter]:.8f}_{time_intervals[interv_iter]:.8f}"].append(data)
                        previous_cases_matrix[f"{thresholds[threshold_iter]:.8f}_{time_intervals[interv_iter]:.8f}"] = trade['x']
                        brk = True

            if brk == True:
                break
            i -= 1

    return config_matrix, trades


if __name__ == "__main__":
    # trades = Bitmex().get_trades_for_period(symbol='XBTUSD', start_time=1545938940000, end_time=1545939000000)
    # cases, trades = get_preventer_cases('XBTUSD', 1545938940000, 1545939000000, [0.003, 0.005, 0.01, 0.0125, 0.015, 0.02], [5000, 15000, 30000, 45000, 60000])
    #
    # with open(f"bitmex_preventer_cases/result.txt", 'w') as f:
    #     json.dump(cases, f)

    # print(res)

    #---------- GENERATE TASK FILE ----------
    # start=1533081600000#1538352000000
    # end=1538352000000#1546300800000
    # interval = 604800000
    #
    # create_splitted_task_file(start=start, end=end, interval=interval, market='XBTUSD',
    #                           thresholds=[0.003, 0.005, 0.01, 0.0125, 0.015, 0.02],
    #                           time_intervals=[5000, 15000, 30000, 45000, 60000])

    #---------- SELECT AND EXECUTE TASK ----------
    # select_and_execute_task()

    #---------- TEST PROXY ----------
    # update_proxy()

    #---------- MERGE TRADES ----------
    # merge_trades()

    while True:
        res = calculate_cases_for_given_trade_batches()
        if res is None:
            break



