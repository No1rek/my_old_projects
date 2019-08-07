import sys
import datetime, time, json
from clients.extended_clients.extended_clients import BinanceCli


class DataScraper:
    intervals = {
        'binance': {
            "1m":60000,            "3m":180000,            "5m":300000,            "15m":900000,
            "30m":1800000,            "1h":3600000,            "2h":7200000,            "4h":14400000,
            "6h":21600000,            "8h":28800000,            "12h":43200000,            "1d":86400000,
            "3d":259200000,            "1w":604800000}
    }

    def show_help(self):
        print("to execute task list from file: python scraper.py fromfile task_filename")
        print("to execute task from shell: python scraper.py run exchange start[milliseconds] end market interval result_filename")

    def save_to_json(self, data, fname):
        with open(fname, 'w') as outfile:
            json.dump(data, outfile)

    def get_task_from_sys_argvs(self):
        task_type = sys.argv[1]
        if task_type == "help":
            self.show_help()
        if task_type == "fromfile":
            task_fname = sys.argv[2]
            tasks = self.get_task_queue_from_file(task_fname)

            for t in tasks:
                data = self.get_dataset(exchange=t['exchange'], start=t['start'], end=t['end'], market=t['market'], interval=t['interval'])
                self.save_to_json(data, f"{t['task_id']}.json")

        if task_type == "run":
            exchange, start, end, market, interval, fname = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
            data = self.get_dataset(exchange=exchange, start=start, end=end, market=market, interval=interval)
            self.save_to_json(data, fname)

    def get_task_queue_from_file(self, fname):
        with open(fname) as f:
            queue = json.load(f)
        return queue

    def get_cli(self, exchange, *args, **kwargs):
        if exchange == 'binance':
            return BinanceCli(*args, **kwargs)

    def get_dataset(self, exchange=None, market=None, start=None, end=None, interval='1m', sleep_interval=0):
        curr_start, total_result, curr_end = None, [], round(datetime.datetime.now().timestamp() * 1000) if end is None else int(end)

        while curr_start is None or curr_end > int(start):
            kwargs = {'symbol': market, 'interval': interval}
            if not (curr_start is None):
                kwargs['start'] = int(curr_start)
            if not (curr_end is None):
                kwargs['end'] = int(curr_end)

            result, result_kwargs = self.get_cli(exchange).get_candle_history(**kwargs)
            time.sleep(sleep_interval)
            total_result = total_result + result

            time_difference = len(result)*self.intervals[exchange][interval]

            if result_kwargs.get('make_break') or len(result) == 0:
                break

            if curr_start is None:
                curr_start = curr_end
                curr_end -= time_difference
                curr_start -= (time_difference + min(time_difference, curr_end - int(start)))
            else:
                curr_end -= time_difference
                curr_start -= min(time_difference, curr_end - int(start))

        sorted_result = sorted(total_result, key=(lambda x:x[0]))
        # cutting redundant candles
        result = []
        for candle in sorted_result:
            if candle[0] >= start and candle[0] <= end:
                result.append(candle)
        return result


if __name__ == "__main__":
    DataScraper().get_task_from_sys_argvs()






