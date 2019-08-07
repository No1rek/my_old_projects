from tools import statisctical_eval, load_trades, save_trades, check_influence_factors, get_cases, dangerous_cases_to_common, get_maximal_price_change_speed, split_by_periods

# # Get data
# save_trades(start=1531958400000, end=1545177600000, market="DATABTC")
# print("Finished!")

# # Influence factors
# market = "NPXSBTC"
# from_time = 0 # 5 months
# volume = 50
# dangerous_period = 10
# trades = load_trades(fname=market)
# cases = get_cases(trades=trades, volume=volume, dangerous_period=dangerous_period)
# factors = check_influence_factors(market=market, cases=cases)
#
# # Dangerous cases to common
# market = "NPXSBTC"
# from_time = 0 # 5 months
# volume = 50
# dangerous_period = 10
#
# trades = load_trades(fname=market)
# cases = get_cases(trades=trades, volume=volume)
# factors = dangerous_cases_to_common(cases=cases, dangerous_period=dangerous_period)
#
# # Speed
# market = "NPXSBTC"
# from_time = 0 # 5 months
# trades = load_trades(fname=market)
# speed = get_maximal_price_change_speed(trades=trades, from_time=from_time)

# # Dangerous cases to common by months
#     market = "NPXSBTC"
#     from_time =  0 # 3 months 1544572800000
#     volume = 50
#     dangerous_period = 10
#
#     trades = load_trades(fname=market)
#     split_interval = 2592000000
#
#     for tr in split_by_periods(trades, split_interval):
#         cases = get_cases(trades=trades, volume=volume, from_time=from_time)
#         print(dangerous_cases_to_common(cases=cases, dangerous_period=dangerous_period))
#
#
#     cases = get_cases(trades=trades, volume=volume, from_time=from_time)
#     print(dangerous_cases_to_common(cases=cases, dangerous_period=dangerous_period))






if __name__ == "__main__":
    # # Get data
    # save_trades(start=1531958400000, end=1545177600000, market="POEBTC")
    # print("Finished!")



    # # Influence factors
    # fname = "DENTBTC"
    # market = "DENT/BTC"
    # from_time = 0 # 1 months  1542585600000
    # volume = 20
    # dangerous_period = 10
    # trades = load_trades(fname=fname)
    # cases = get_cases(trades=trades, volume=volume, dangerous_period=dangerous_period, from_time=from_time)
    # factors = check_influence_factors(market=market, cases=cases, btc_periods_to_compare=12)
    # print(factors)





    # Dangerous cases to common
    market = "POEBTC"
    from_time =  1544572800000 #  1 months  1542585600000  3 months 1536710400000
    volume = 2.5
    dangerous_periods = [2.5, 5, 7.5, 10]
    dangerous_period = 10

    trades = load_trades(fname=market)
    split_interval = 2592000000
    splitted = split_by_periods(trades, split_interval)
    print([(float(splitted[i][-1]['T']) - float(splitted[i - 1][-1]['T']))/2592000000 for i in range(1, len(splitted))])
    #
    # for tr in splitted:
    #     cases = get_cases(trades=tr, volume=volume, from_time=from_time)
    #     print(dangerous_cases_to_common(cases=cases, dangerous_period=dangerous_period))
    #
    cases = get_cases(trades=trades, volume=volume, from_time=from_time)
    # print(statisctical_eval(cases))

    # for dp in dangerous_periods:
    #     print(dangerous_cases_to_common(cases=cases, dangerous_period=dp))

    # Speed
    market = "POEBTC"
    from_time = 0 # 1 week
    trades = load_trades(fname=market)
    speed = get_maximal_price_change_speed(trades=trades, from_time=from_time)
    print(speed)
    print(speed['speed']*3600*24)