import requests
import json
import time
import datetime
import urllib
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import urllib.parse as urlpar
import hmac,hashlib 

# Расстояние от курса в процентах
PERCENT_DISTANCE = 0.12
# Валюты, на которых торговать
CURR_TO_TRADE = ['XMR_MAID','XMR_BTCD','XMR_NXT'] #, 'XMR_BCN'
#Через такое кол-во секунд оно будет подправлять ордеры(не слишком часто, чтобы оно ну убегало от взлетов)
move_time = 15
# Часть общего капитала на один ордер в процентах
partOfUsedCapita = 0.1

APIKey = "QWERTY"
Secret = "QWERTY"

PROXY = {'http': '1.1.1.1:8000'}
AUTH = ("9Z3w8S", "Ksc8HK")

#Проверяем работает ли прокси
def check_proxy():
	global PROXY
	global AUTH
	try:requests.get("http://google.com",proxies=PROXY, auth = AUTH)
	except IOError:
		return False
	return True

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

def post_process(before):
	after = before
	# Add timestamps if there isnt one but is a datetime
	if('return' in after):
		if(isinstance(after['return'], list)):
			for x in xrange(0, len(after['return'])):
				if(isinstance(after['return'][x], dict)):
					if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
	return after	
	
def api_query(command,req={},prox = False):
	global APIKey 
	global Secret
	global PROXY
	global AUTH
	
	if PROXY['http'] == "":
		prox = False
	
	
	if(command == "returnTicker" or command == "return24Volume"):
		ret = requests.get('https://poloniex.com/public?command=' + command, proxies=PROXY)
		return json.loads(ret.text)
	elif(command == "returnOrderBook"):
		ret = requests.get('https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair']), proxies=PROXY)
		return json.loads(ret.text)
	elif(command == "returnMarketTradeHistory"):
		ret = requests.get('https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(req['currencyPair']), proxies=PROXY)
		return json.loads(ret.text)
	else:	
		req['command'] = command
		req['nonce'] = int(time.time()*1000)
		post_data = urllib.parse.urlencode(req)
		sign = hmac.new(bytearray(Secret, "ASCII") , bytearray(post_data, "ASCII") , hashlib.sha512).hexdigest()
		headers = {'Sign':sign, 'Key':APIKey}
		if prox is True:
			ret = requests.post(url = 'https://poloniex.com/tradingApi', data = req , headers=headers, proxies=PROXY, auth=AUTH)
		if prox is False:
			ret = requests.post(url = 'https://poloniex.com/tradingApi', data = req , headers=headers)
		
		
		try: 
			jsonRet = json.loads(ret.text)
		except IOError:
			return []
		return post_process(jsonRet)	

def balances():
	return api_query("returnCompleteBalances")
	
def cancel(currencyPair,orderNumber):
    return api_query('cancelOrder',{"currencyPair":currencyPair,"orderNumber":str(orderNumber), "postOnly" : "1"})	

def move(currencyPair, orderNumber,rate):
	ret = api_query('moveOrder',{"currencyPair":currencyPair, "orderNumber":orderNumber,"rate":str(rate)})
	if ret.get('error',False) != False:
		print(ret)
	return 	ret	

def returnTicker():
	global PROXY
	global AUTH
	ret = requests.get('https://poloniex.com/public?command=returnTicker', proxies=PROXY, auth = AUTH)
	return json.loads(ret.text)

def returnOpenOrders(currencyPair='all'):
	return api_query('returnOpenOrders',{"currencyPair":currencyPair})

def sell(currencyPair,rate,amount,fillOrKill=0):
	ret = api_query('sell',{"currencyPair":str(currencyPair),"rate":str(rate),"amount":str(amount), "fillOrKill":str(fillOrKill)})
	if ret.get('error',False) != False:
		print(ret)
		return False
	return 	ret

def buy(currencyPair,rate,amount, fillOrKill=0):
	ret = api_query('buy',{"currencyPair":str(currencyPair),"rate":str(rate),"amount":str(amount), "fillOrKill":str(fillOrKill)})
	if ret.get('error',False) != False:
		print(ret)
		return False
	return 	ret

def returnOrderBook (currencyPair='all', prox=False):	
	book = api_query("returnOrderBook", {'currencyPair': currencyPair},prox)
	return book	

#----------------------------------------------------------------------	
#Функция возвращает цену и количество валюты на которые нужно выставить ордер, чтобы потратить BTCToSpend валюты на покупку
def to_buy(pair, BTCToSpend):
	global book
	amount = 0
	total = 0
	for i in book[pair]['asks']:
		if BTCToSpend < total:
			amount += (BTCToSpend - total)/float(i[0])
			return [float(i[0]), amount]
		else:
			amount += float(i[1])
			total += float(i[0])*float(i[1])	
			
#Возвращает цену, по которой нужно продать количество amount чтобы заполнитьордер полностью
def to_sell(pair, amount):
	global book
	for i in book[pair]['bids']:
		amount -= float(i[1])
		if amount < 0:
			return float(i[0])

#Считает спред			
def sprede(pair):
	global ticker
	return (float(ticker[pair]['lowestAsk'])/float(ticker[pair]['highestBid']) - 1)*100

#Выставляет ордера на покупку/продажу	
def place_orders():
	global ORDERS
	global CN
	global BALANCE
	global PERCENT_DISTANCE
	global ticker
	global CURR_TO_TRADE
	global BTC_PER_ACTION
	global XMR_PER_ACTION

	for pair in ticker.keys():

		#Если пара в списке валют для торговли И спред меньше 3%(чтобы оно вы выставляло закупку сразу после скачка)
		if pair in CURR_TO_TRADE and sprede(pair)<3:				
			#buy
			present = False
			# Смотрим висят ли уже ордера на этой валюте
			if ORDERS.get(pair,False) != False:
				for ord in ORDERS[pair]:
					if ord['type'] == 'buy':
						present = True

			# Если нет:
			if present is False:

				# Если на акке хватает монеро на выставление ордера:
				if float(BALANCE['XMR']['available'])*float(ticker['BTC_XMR']['lowestAsk']) >= BTC_PER_ACTION and CN < 6:
					
					amount = XMR_PER_ACTION/(float(ticker[pair]['highestBid']))
					amount = round(amount, 5) - 0.00001
					
					print('PLACE BUY ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE['XMR']) 
					
					buy(pair, float(ticker[pair]['highestBid'])*(1 - PERCENT_DISTANCE), amount)

					CN += 1
				elif CN < 5:
					# Покупаем сначала монеро
					price = to_buy('BTC_XMR', BTC_PER_ACTION - float(BALANCE['XMR']['available'])*float(ticker['BTC_XMR']['lowestAsk']))[0]
					amount = to_buy('BTC_XMR', BTC_PER_ACTION - float(BALANCE['XMR']['available'])*float(ticker['BTC_XMR']['lowestAsk']))[1]
					amount = round(amount, 5) - 0.00001
					print('BUY XMR TO PLACE BUY ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE['BTC']) 
					
					b = buy('BTC_XMR', price, amount,1) 
					CN += 1
					
					if b != False:
						BALANCE['XMR']['available'] = str(float(BALANCE['XMR']['available']) + float(amount)*(0.9975))
					
					# А потом ставим ордер на покупку
					amount = float(BALANCE['XMR']['available'])/float(ticker[pair]['highestBid'])*(1 - PERCENT_DISTANCE)
					amount = round(amount, 5) - 0.00001
					
					print('PLACE BUY ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE['XMR']) 
					b = buy(pair, float(ticker[pair]['highestBid'])*(1 - PERCENT_DISTANCE), amount)
					
					if b != False:
						BALANCE['XMR']['available'] = str(float(BALANCE[pair[pair.find('_')+1:]]['available']) - float(amount)*(1.0025))
					
					CN += 1
					
			if CN == 6:
				break
			#sell
			
			present = False
			if ORDERS.get(pair,False) != False:
				for ord in ORDERS[pair]:
					if ord['type'] == 'sell':
						present = True


			
			if present is False:
				pair1 = 'BTC_'+pair[pair.find('_')+1:]
				
				if float(BALANCE[pair[pair.find('_')+1:]]['available'])*float(ticker['BTC_'+pair[pair.find('_')+1:]]['lowestAsk']) >= BTC_PER_ACTION and CN < 6:
					price = float(ticker[pair]['lowestAsk'])*(1 + PERCENT_DISTANCE)
					amount = XMR_PER_ACTION/price  - 0.00001
					
					print('PLACE SELL ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE[pair[pair.find('_')+1:]]) 
					b = sell(pair, price, amount)
					
					if b != False:
						BALANCE[pair[pair.find('_')+1:]]['available'] = str(float(BALANCE[pair[pair.find('_')+1:]]['available']) - float(amount))
					
					CN += 1
				elif CN < 5:
					pair1 = 'BTC_'+pair[pair.find('_')+1:]
					price = to_buy(pair, BTC_PER_ACTION/float(ticker['BTC_XMR']['lowestAsk']))[0]
					amount = to_buy(pair, BTC_PER_ACTION/float(ticker['BTC_XMR']['lowestAsk']) - float(BALANCE[pair[pair.find('_')+1:]]['available'])*float(ticker[pair1]['lowestAsk']))[1]  #/float(ticker['BTC_XMR']['highestBid'])
					amount = round(amount, 5) - 0.00001
					
					print('BUY CURR TO PLACE SELL ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE['BTC']) 
					
					b = buy(pair1, price, amount,1)
					CN += 1
					
					if b != False:
						BALANCE[pair[pair.find('_')+1:]]['available'] = str(float(BALANCE[pair[pair.find('_')+1:]]['available']) + float(amount)*(0.9975))
					CN += 1
						
					price = float(ticker[pair]['lowestAsk'])*(1 + PERCENT_DISTANCE)
					amount = float(BALANCE[pair[pair.find('_')+1:]]['available'])
					amount = round(amount, 5) - 0.00001
					
					print('PLACE SELL ORDER '+pair+ " amount "+ str(amount))
					print(BALANCE[pair[pair.find('_')+1:]]) 
					
					b = sell(pair, price, amount)
					
					if b != False:
						BALANCE[pair[pair.find('_')+1:]]['available'] = str(float(BALANCE[pair[pair.find('_')+1:]]['available']) - float(amount)*(1.0025))
					CN += 1
					
					print('SELL '+ pair)
					
			if CN == 6:
				break

def move_orders(pair0=0,t='w'):
	global ORDERS
	global CN 
	global ticker
	global PERCENT_DISTANCE
	global CURR_TO_TRADE
	global BTC_PER_ACTION
	global XMR_PER_ACTION
	
	key = list(ORDERS.keys())
	key = key[pair0:]
	
	for pair in key:
		if pair in CURR_TO_TRADE and sprede(pair)<3:		
			for ord in ORDERS[pair]:
				if ord['type'] == 'buy' and CN < 6  and  (t == 'b' or t == 'w'):
					if abs(float(ord['rate']) - float(ticker[pair]['highestBid'])*(1.0 - PERCENT_DISTANCE))/float(ticker[pair]['highestBid'])*(1.0 - PERCENT_DISTANCE) > 0.02:
						m= move(pair, ord['orderNumber'], float(ticker[pair]['highestBid'])*(1.0 - PERCENT_DISTANCE))
						print('MOVE BUY ORDER '+ pair)
						
						if m.get('error',False) != False:
							if m['error'] == 'Not enough XMR.':
								if CN < 6:
									cancel(pair, ord['orderNumber'])
									CN += 1
								else:
									return [ORDERS[pair].index(ord),'b']
						
						CN += 1
						t = 'w'
				elif ord['type'] == 'buy' and CN == 6 and abs(float(ord['rate']) - float(ticker[pair]['highestBid'])*(1.0 - PERCENT_DISTANCE))/float(ticker[pair]['highestBid'])*(1.0 - PERCENT_DISTANCE) > 0.02 and(t == 'b' or t == 'w'):
					return [ORDERS[pair].index(ord),'b']
				
				elif ord['type'] == 'sell' and CN < 6  and (t == 's' or t == 'w'):
					if abs(float(ord['rate']) - float(ticker[pair]['lowestAsk'])*(1.0 + PERCENT_DISTANCE))/float(ticker[pair]['lowestAsk'])*(1.0 + PERCENT_DISTANCE) > 0.02:
						move(pair, ord['orderNumber'], float(ticker[pair]['lowestAsk'])*(1.0 + PERCENT_DISTANCE))
						print('MOVE SELL ORDER '+ pair)
						CN += 1
						t = 'w'
				elif ord['type'] == 'sell' and CN == 6 and  abs(float(ord['rate']) - float(ticker[pair]['lowestAsk'])*(1.0 + PERCENT_DISTANCE))/float(ticker[pair]['lowestAsk'])*(1.0 + PERCENT_DISTANCE) > 0.02 and (t == 's' or t == 'w'):
					return [ORDERS[pair].index(ord),'s']
	return [0,'w']
		
	
def sell_extra():
	global ticker
	global BALANCE
	global CN
	global CURR_TO_TRADE
	global ORDERS
	global BTC_PER_ACTION
	global XMR_PER_ACTION
	for pair in BALANCE:
		if ticker.get('XMR_'+pair, False) != False and CN < 6:
			present = False

			if ORDERS.get('XMR_'+pair,False) != False:
				if len(ORDERS['XMR_'+pair]) >= 2:
					present = True


			if present == True:
				amount = float(BALANCE[pair]['available'])
				amount = amount - 0.00001
				
				price = to_sell('BTC_'+pair, amount)
				
				if float(amount)*float(price) > 0.0001:
					print('SELL EXTRA '+ pair+ ' amount ' + str(amount))
					print(BALANCE[pair])
					sell('BTC_'+pair, price, amount, 1)
					
					CN += 1
		
		if  pair == 'XMR' and CN < 6:
			
			amount = float(BALANCE[pair]['available']) - XMR_PER_ACTION
			amount = round(amount, 5) - 0.00001
			
			price = to_sell('BTC_'+pair, amount)
			
			if float(amount)*float(price) > 0.0001:
				print('SELL EXTRA '+ pair+ ' amount ' + str(amount))
				print(BALANCE[pair])
				sell('BTC_'+pair, price, amount, 1)
				
				CN +=1

timer = 0		


def cancel_orders():
	global ORDERS
	global CN
	global CURR_TO_TRADE
	global BTC_PER_ACTION 
	global XMR_PER_ACTION
	global BALANCE
	global ticker

	for pair in ORDERS.keys():
		b = 0
		s = 0
		if ORDERS.get(pair,False) != False and pair in CURR_TO_TRADE:
			for ord in ORDERS[pair]:
				if ord['type'] == 'buy' and CN < 6:
					if b == 0:
						b += 1
					elif float(ord['total']) < BTC_PER_ACTION - 0.0001 and float(BALANCE[pair[pair.find('_')+1:]]['available'])*float(ticker['BTC_'+pair[pair.find('_')+1:]]['lowestAsk']) > 0.0002:
						print('CANCEL BUY ORDER TO REPLACE '  + pair )
						print(float(ord['total']))
						cancel(pair, ord['orderNumber'])
					else:
						print('CANCEL 2ND BUY ORDER')
						cancel(pair, ord['orderNumber'])
						
				if ord['type'] == 'sell' and CN < 6:
					if s == 0:
						s += 1
					elif float(ord['total']) < BTC_PER_ACTION - 0.0001 and float(BALANCE[pair[pair.find('_')+1:]]['available'])*float(ticker['BTC_'+pair[pair.find('_')+1:]]['highestBid']) > 0.0002:
						print('CANCEL SELL ORDER TO REPLACE '  + pair )
						print(float(ord['total']))
						cancel(pair, ord['orderNumber'])						
					else:
						print('CANCEL 2ND SELL ORDER')
						cancel(pair, ord['orderNumber'])
						
						
					
						
def total_balance():
	global BALANCE
	total = 0.0
	for pair in BALANCE.keys():
		total += float(BALANCE[pair]['btcValue'])
	return total
	
if check_proxy() is True:
	BALANCE = balances()	
	total0 = total_balance()	
	time.sleep(1)	


pair0 = 0	
t = 'w'
while True:
	CN = 0

	if check_proxy() is True:
		 
		ticker = returnTicker()
		book = returnOrderBook ('all', True)
		BALANCE = balances()
		CN += 1
		ORDERS = returnOpenOrders()
		CN += 1
		if BALANCE.get('BTC',False) !=False and book.get('BTC_XMR',False) !=False and ticker.get('BTC_XMR',False) !=False:
			total = total_balance()
			print('TOTAL '+ str(total)+ ' | %F' % (float(total)/float(total0) - 1))		
			BTC_PER_ACTION = 0
			if BTC_PER_ACTION == 0:
				BTC_PER_ACTION = round(float(total)*partOfUsedCapita,4)
				price = (float(ticker['BTC_XMR']['lowestAsk'])+float(ticker['BTC_XMR']['highestBid']))/2
				XMR_PER_ACTION = round(BTC_PER_ACTION/price,4)

			if pair0 != 0 or t != 'w' :
				moved =  move_orders(pair0,t)
				pair0 = moved[0]
				t = moved[1]

			if timer % move_time == 0:
				moved =  move_orders(0,'w')
				pair0 = moved[0]
				t = moved[1]
			
			
			place_orders()		
			sell_extra()
			cancel_orders()

		timer += 1
		time.sleep(1)
	else:
		print('Proxy is not working')
		timer += 1
		time.sleep(1)