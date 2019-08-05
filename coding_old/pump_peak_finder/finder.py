# -*- coding: utf-8 -*-

import math
import numpy 
import requests
import json
import time
import datetime

numpy.seterr(divide='ignore', invalid='ignore')

#parabol = numpy.polyfit(x,y,2) # полином второго порядка
#logar = numpy.polyfit(numpy.log(x), y, 1) #y = a log(x) + b
#sqrf = numpy.polyfit(x, numpy.log(y), 1, w=numpy.sqrt(y)) # y = exp(1.42) * exp(0.0601 * x) = 4.12 * exp(0.0601 * x)
parabol = numpy.array([0]);

def pologetstats(stime, ctime, pair):
	if str(stime).find(":") > -1:
		stime = float(time.mktime(datetime.datetime.strptime(str(stime), "%d-%m-%y %H:%M:%S").timetuple()))
	if str(ctime).find(":") > -1:
		ctime = float(time.mktime(datetime.datetime.strptime(str(ctime), "%d-%m-%y %H:%M:%S").timetuple()))
		
	ret = requests.get('https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(pair) + "&start=" + str(stime) + "&end=" + str(ctime) )
	ret = ret.text
	ret = numpy.array(json.loads(ret))
	i = ret.shape[0]
	i = i - 1
	x = numpy.array([])
	y = numpy.array([])
	temp = {}
	for r in ret:
		temp = ret[i]
		#x =  #2017-05-30 15:20:45
		
		normedtime = float(time.mktime(datetime.datetime.strptime(temp.get("date"), "%Y-%m-%d %H:%M:%S").timetuple())) - float(stime) #нормируем, уменьшаем числа
		x = numpy.append(x, [normedtime])
		y = numpy.append(y,[float(temp.get("rate"))])
		i = i - 1
	if(x.size > 0):
		x = x + abs(numpy.amin(x))	#избавляемся от отрицательных значений
	xy = numpy.array([x,y])
	return xy
		
def linfunc(q,s,b):
	ret = s * q + b
	return ret
def polfunc(q,s,b,c):
	ret = s * q ** 2 + b * q + c
	return ret
def sqrfunc(q, s, b):
	ret = s*(math.sqrt(q)) + b
	return ret

def stoplimit(buypr ,currentpr, lastResult=0.00,exr_intervals=[-0.015,0.03,0.7,0.11]):
	i = 0
	for u in exr_intervals:
		if i + 1 == len(exr_intervals) and lastResult > u:
			return True
		elif (buypr/currentpr - 1 <= u and lastResult > u and lastResult<exr_intervals[i+1]):
			return True
		elif buypr/currentpr - 1 <= exr_intervals[0]:
			return True
		else: 
			return False
		i = i + 1

	
def sell(pair, x0=None,y0=None, buyprice=0, currentprice=0, mimNumberOfTradesBefore=100, accur=12, testmod=False, startTime=0, currentTime=0):
	if (x0 is None  and y0 is None):
		xy = pologetstats(startTime, currentTime, pair)
		numOfTrades = xy[0].shape[0]
		x = numpy.array(xy[0])
		y = numpy.array(xy[1])
	else:
		numOfTrades = x0.shape[0]
		x = numpy.array(x0)
		y = numpy.array(y0)

	
	
	if testmod:
		xy = pologetstats(startTime, currentTime, pair)
		return [x,y,numOfTrades]

	elif numOfTrades > mimNumberOfTradesBefore:
		
		#Умножаем для повышения точности коэфициенто
		y = y*100
				
		parabol = numpy.polyfit(x,y,2)
		sqrf = numpy.polyfit(numpy.sqrt(x), y, 1)
		linf = numpy.polyfit(x, y, 1)
		
		ax = x[numOfTrades - 2 - accur:numOfTrades - 2]
		ay = y[numOfTrades - 2 - accur:numOfTrades - 2]
			

		j = 0;
		delta = 0.0
		deltasqr = 0.0
		deltalin= 0.0
		deltapol= 0.0
		check = True
		# Проверяем отклонилась ли парабола от остальных функций
		for a in numpy.nditer(ax):
			if(j > 0):
				deltapol = deltapol + (polfunc(ax[j], polfunc[0], polfunc[1], polfunc[2]) - ay[j]) - (polfunc(ax[j-1], polfunc[0], polfunc[1], polfunc[2]) - ay[j-1])
				deltasqr = deltasqr + (sqrfunc(ax[j], sqrf[0], sqrf[1]) - ay[j]) - (sqrfunc(ax[j-1], sqrf[0], sqrf[1]) - ay[j-1])
				deltalin = deltalin + (linfunc(ax[j], linf[0], linf[1]) - ay[j]) - (linfunc(ax[j-1], linf[0], linf[1]) - ay[j-1])
				j = j + 1
				#delta = delta +  ay[j] - ay[j-1]
		if( min([deltasqr,deltalin])<0 and deltapol>0):
				check = False
			
		if (y[numOfTrades - 1] - y[numOfTrades - 1 - accur] > 0 ):
			check = False
		
		deviasumsqr = 0.0
		deviasumpol = 0.0
		deviasumlin = 0.0


		#Смотрим, стоит ли является ли динамический ряд прогнозируемым впринципе, ищем отклонение и ливаем, если он слишком большой	
		j = 0
		
		mean = 0
		for a in numpy.nditer(x):
			deviasumsqr = float((deviasumsqr + (y[j] - sqrfunc(x[j], sqrf[0], sqrf[1])))**2)
			deviasumlin = float((deviasumlin + (y[j] - linfunc(x[j], linf[0], linf[1])))**2)
			deviasumpol = float((deviasumpol + (y[j] - polfunc(x[j], parabol[0], parabol[1], parabol[2])))**2)
			mean = mean + y[j]
			j = j + 1
		
		if (math.sqrt((deviasumpol-min([deviasumsqr,deviasumlin]))**2)/min([deviasumsqr,deviasumlin]) < 0.1): # настроить параметр, строка отвечает за примерно прямой тренд
			deviation = math.sqrt(min([deviasumsqr,deviasumlin])/j)
			mean = mean/j
			if deviation/mean > 0.66:
				check = False
		
		# Проверяем, направлены ли ветки параболы вниз
		vershina = -1 * parabol[1] / (2 * parabol[0])
		#Предохраняемся от того, чтобы это не была тупо спадающая ветка параболы
		if(parabol[0] > 0 or check or vershina < x[(numOfTrades - 1)//2]): #vershina > x[numOfTrades - 1] or vershina < x[(numOfTrades - 1)//2] or
			return False
		else:
			return True
	else:		
		return False	

