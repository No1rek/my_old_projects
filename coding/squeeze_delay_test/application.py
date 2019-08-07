import sys
from analyzer import Analyzer
from squeeze_scraper import SqueezeScraper
from plotter import Plotter

class App:
    def __init__(self):
        self.interval = 0.5 # seconds
        self.case_count = 500
        self.candle_group_count = 6
        self.time_before_after_bk_candle = 30000 # milliseconds
        self.threshold = 0.0005
        self.period = 5

        self.scraper = SqueezeScraper()
        self.analyser = Analyzer()
        self.plotter = Plotter()

    def run(self, mode=None):
        if mode is None:
            mode = sys.argv[1]

        if mode == "data_scrap":
            tasks = self.scraper.load_tasks()
            ret = []
            for t in tasks:
                units = t["units"]
                cases = self.scraper.find_candle_squeezes(t, self.case_count, self.time_before_after_bk_candle, group_split_count=self.candle_group_count)
                ret.append(t)
                ret[-1]["cases"] = []
                print(len(cases))
                for i in range(len(cases)):
                    print(f"Progress {round(i/len(cases)*100,3)}%")
                    start, end = cases[i]
                    ret[-1]["cases"].append(self.scraper.get_trades_for_case(units, start, end))
            self.scraper.save_case_timings(ret)
        if mode == "analyze":
            tasks = self.scraper.load_tasks(fname="tasks_with_cases")
            for t in tasks:
                cases = t["cases"][::-1]
                for c in cases:
                    try:
                        case_to_plot, bks = {}, {}
                        for ex, data in c.items():
                            x = [int(float(x)/1000) for x in data["x"]]
                            y = [float(y) for y in data["y"]]
                            x, y = self.analyser.interpolate(x, y, self.interval)
                            y = self.analyser.smooth(y, period=self.period)
                            bks[ex] = self.analyser.find_break_moments(x, y, threshold=self.threshold)
                            case_to_plot[ex] = {"x":x, "y": y}
                        for ex, data in case_to_plot.items():
                            if len(data["x"]) < 10:
                                raise Exception
                    except:
                        continue
                    # Append there function to calculate global report
                    self.plotter.plot(case=case_to_plot, bks=bks)
        if mode == "optimize":
            from misc.config import smooth_intervals, thresholds, interpolate_periods, expected_change
            tasks = self.scraper.load_tasks(fname="tasks_with_cases")
            for t in tasks:
                cases = t["cases"]
                configs = self.analyser.optimize_config(base_ex="binance", compare_ex="bitmex",
                                              cases=cases, smooth_intervals=smooth_intervals, thresholds=thresholds,
                                              interpolate_periods=interpolate_periods, expected_change=expected_change,
                                              entrance_time=1, stop=0.33, commision=0.0005)
                import pprint

                pp = pprint.PrettyPrinter(indent=4)

                pp.pprint(configs)


if __name__ == "__main__":
    App().run(mode="optimize")