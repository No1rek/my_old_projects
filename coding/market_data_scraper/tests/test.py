from scraper import DataScraper

def test_dataset_correctness():
    exchange = 'binance'
    start = 1542043176000
    end = 1542043236000
    market = 'ETH/BTC'
    interval = '1m'

    result = DataScraper().get_dataset(exchange=exchange, start=start, end=end, interval=interval, market=market)
    print((end - start)/3600000)
    print((result[-1][0] - result[0][0])/3600000)
    print(len(result))
    print(result)


if __name__ == "__main__":
    test_dataset_correctness()


