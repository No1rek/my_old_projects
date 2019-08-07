import numpy as np
import talib
import math
from misc.binary_search import binarySearch


class Analyzer:
    def __init__(self):
        pass

    def interpolate(self, x, y, interval=1):
        xp = np.array(x)
        yp = np.array(y)
        x = [round(xp[0])]

        while x[-1] < float(xp[-1]):
            x.append(x[-1] + interval)

        x = np.array(x)
        y = np.interp(x, xp, yp)
        return x, y

    def HMA(self, y, period=30):
        y = np.array(y)
        n = period
        n_2 = round(period / 2)
        sqrt_n = round(math.sqrt(n))
        WMA = talib.WMA
        return WMA(2 * WMA(y, n_2) - WMA(y, n), sqrt_n).tolist()

    def smooth(self, y, period=30):
        return self.HMA(y, period=period)

    def find_break_moments(self, x, y, threshold):
        bks = []
        for i in range(1,len(x),1):
            if abs(y[i]/y[i-1] - 1) > threshold:
                j = i

                while j < len(x):
                    if abs(y[j]/y[j-1] - 1) > threshold:
                        j += 1
                    else:
                        break
                start = i - 1
                end = j - 1
                bks.append({"duration": x[end] - x[start], "change":y[end]/y[start], "start": {"x": x[start], "y":y[start]}, "end":{"x":x[end], "y":y[end]}})

        return bks

    def open_close_on_parallel_exchange(self, entrance_x, change, expected_change, stop, neutral, x, y, commision):
        # p - profit, n - neutral, l - loss
        i = binarySearch(x, entrance_x)
        count = len(x)
        j = i + 1
        open_p = y[i]
        real_expected_change = change*expected_change
        stop = -real_expected_change*stop
        neutral = real_expected_change*stop

        if change - 1 > 0:
            while j < len(y) - 1:
                if (y[j] / y[i] - 1)*(1 - commision)*(1 - commision) >= real_expected_change:
                    close_p = y[j + 1]
                    return open_p, close_p, 'p'
                if (y[j] / y[i] - 1)*(1 - commision)*(1 - commision) <= stop:
                    close_p = y[j + 1]
                    return open_p, close_p, 'l'
                j += 1
        else:
            while i < len(y) - 1:
                if (y[j] / y[i] - 1)*(1 - commision)*(1 - commision) <= real_expected_change:
                    close_p = y[j]
                    return open_p, close_p, 'p'
                if (y[j] / y[i] - 1)*(1 - commision)*(1 - commision) >= stop:
                    close_p = y[j]
                    return open_p, close_p, 'l'
                j += 1
        close_p = y[-1]
        # result = close_p/open_p
        result = close_p/open_p*(1 - commision)*(1 - commision)
        if abs(result - 1) <= neutral:
            return open_p, close_p, 'n'
        if change > 0 and result -1 > 0 :
            return open_p, close_p, 'p' #p
        elif change < 0 and result -1 < 0 :
            return open_p, close_p, 'p' #p
        else:
            return open_p, close_p, 'l' #l


    def optimize_config(self, base_ex, compare_ex, cases, smooth_intervals, thresholds, interpolate_periods, expected_change, stop=0.33, neutral=0.2, entrance_time=1, commision=0.001, return_entrance_points=False):
        # r - result, p - profit, n - neutral, l - loss, pr,nr,lr - results for each case
        configs = {}
        for i in interpolate_periods:
            for s in smooth_intervals:
                for t in thresholds:
                    for e in expected_change:
                        configs[f"{i}_{s}_{t}_{e}"] = {"r":1, "p":0, "n":0, "l":0, "pr":1, "nr":1, "lr":1, "positions":[]}

        total_iterations = len(cases)*len(interpolate_periods)*len(smooth_intervals)*len(thresholds)
        progress = 0

        for c in cases:
            base, compare = None, None
            for ex in c.keys():
                if ex.find(base_ex) > -1:
                    base = c[ex]
                if ex.find(compare_ex) > -1:
                    compare = c[ex]
            if base is None or compare is None:
                continue

            x_b = [int(float(x) / 1000) for x in base["x"]]
            y_b = [float(y) for y in base["y"]]
            x_c = [int(float(x) / 1000) for x in compare["x"]]
            y_c = [float(y) for y in compare["y"]]
            for i in interpolate_periods:
                try:
                    x1, y1 = self.interpolate(x_b, y_b, i)
                    for s in smooth_intervals:
                        try:
                            if s > len(y1):
                                continue
                            ys = self.smooth(y1, period=s)
                            for t in thresholds:
                                progress += 1
                                # print(progress/total_iterations)

                                base_ex_bks = self.find_break_moments(x1, ys, t)
                                for e in expected_change:
                                    if len(base_ex_bks) > 0:
                                        open_p, close_p, trade_type = self.open_close_on_parallel_exchange(base_ex_bks[0]["start"]["x"]+entrance_time+i, base_ex_bks[0]["change"], e, stop, neutral, x_c, y_c, commision)
                                        # result = close_p/open_p
                                        result = close_p/open_p*(1 - commision)*(1 - commision)
                                        configs[f"{i}_{s}_{t}_{e}"]["r"] *= result
                                        configs[f"{i}_{s}_{t}_{e}"][trade_type] += 1
                                        configs[f"{i}_{s}_{t}_{e}"][trade_type+"r"] *= result
                                        if return_entrance_points:
                                            configs[f"{i}_{s}_{t}_{e}"]["positions"].append([open_p,close_p])
                        except:
                            import traceback
                            print(traceback.format_exc())
                except:
                    import traceback
                    print(traceback.format_exc())

        def sort_res(x):
            if x[1]["l"] == 0:
                return 0
            else:
                return x[1]["p"]/x[1]["l"]

        configs = [c for c in sorted(configs.items(), key=lambda x: x[1]["r"],reverse=True) if c[1]['r'] != 1][:300]
        # configs = sorted(configs.items(), key=sort_res, reverse=True)[:100]
        return configs