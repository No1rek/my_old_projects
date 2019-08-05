import numpy as np
import scipy
#from scipy import stats
import sqlite3
import re
import math
from functools import reduce



def analysis(arr_name, arr, arr2=[], UNC=False):
	ret = ''
	grouped = group(arr)
	if UNC:
		grouped = groupUNC(arr)
	ret += '-----%s-------------------- \n' % arr_name
	for i in grouped:
		ret += '%s: %s \n' % (str(i), str(grouped[i]))
	ret += 'Розмір вибірки %s \n' % str(len(arr))
	ret += 'Найменше значення %s \n' % str(np.amin(arr))
	ret += 'Найбільше значення %s \n' % str(np.amax(arr))
	ret += 'Розмах %s \n' % str(np.ptp(arr))
	ret += 'Медіана %s \n' % str(np.median(arr))
	ret += 'Середнє арифметичне %s \n' % str(np.mean(arr))
	ret += 'Стандартне відхилення %s \n' % str(np.std(arr))
	ret += 'Дисперсія %s \n' % str(np.var(arr))
	if arr2:
		ret += 'Коефіцієнт кореляції Пірсона %s \n' % str(np.corrcoef(arr,arr2)[0][1])
		#ret += 'Перехресна кореляція %s \n' % str(stats.spearmanr(arr,arr2))
	#ret = '%s /n' % str()
	ret += '----------------------------------- \n'
	return ret
def group(arr):
	narr = np.array([arr])
	min = 18
	max = 60
	l = len(arr)	
	m = 7
	h = 6
	x0 = 18
	x1 = 18 + 6
	res = {}
	while x0 < max:
		res["{0} - {1}".format(x0,x1)] = len([x for x in arr if (x> x0 and x<=x1)])
		x0 += h
		x1 += h
	return res
	
def groupUNC(arr):
	narr = np.array([arr])
	min = np.amin(arr)
	max = np.amax(arr)
	l = len(arr)	
	m = round(1 + 3.322*math.log10(l), 0)
	h = round((max-min)/m,0)
	x0 = min
	x1 = min + h
	res = {}
	while x0 < max:
		res["{0} - {1}".format(x0,x1)] = len([x for x in arr if (x> x0 and x<=x1)])
		x0 += h
		x1 += h
	return res
	

conn = sqlite3.connect('data.db')
c = conn.cursor()

#TOTAL

def getStats():
	STATS = {'kv':[],'kh':[],'od':[],'dp':[],'zp':[],'lv':[],'nk':[],'vn':[],'zt':[],'other':[]}
	for city in ['kv','kh','od','dp','zp','lv','nk','vn','zt','other']:
		STATS[city] = {'arr_wage':[], 'arr_age':[],'arr_agemin':[] , 'arr_agemin':[], 'len':0, 'aged_len':0 }
		STATS[city]['arr_wage'] = STATS[city]['arr_wage'] + [i[0] for i in list(c.execute("SELECT wage FROM %s WHERE (agemin>0 OR agemax>0) AND wage > 0" % (city)))]
		STATS[city]['arr_age'] = STATS[city]['arr_age'] + [i for i in list(c.execute("SELECT agemin, agemax FROM %s WHERE (agemin>0 OR agemax>0) AND wage > 0" % (city)))]
		STATS[city]['arr_agemin'] = [(lambda x: x if x > 0 else 18)(i[0]) for i in STATS[city]['arr_age']]
		STATS[city]['arr_agemax'] = [(lambda x: x if x > 0 else 60)(i[1]) for i in STATS[city]['arr_age']]
		STATS[city]['arr_age_range'] = [((lambda x: x if x > 0 else 60)(i[1]) - max(i[0],18)) for i in STATS[city]['arr_age']]
		STATS[city]['len'] = len(list(c.execute("SELECT * FROM %s " % (city)) ))
		STATS[city]['aged_len'] = len(list(c.execute("SELECT * FROM %s WHERE (agemin>0 OR agemax>0)" % (city))))
		
	TOTAL = {'arr_wage':[], 'arr_age':[],'arr_agemin':[] , 'arr_agemin':[], 'len':0, 'aged_len':0 }
	TOTAL['arr_wage'] = list(reduce((lambda x,y: x + y),[STATS[key]['arr_wage'] for key in STATS]))
	TOTAL['arr_age'] = list(reduce((lambda x,y: x + y),[STATS[key]['arr_age'] for key in STATS]))
	TOTAL['arr_agemin'] = list(reduce((lambda x,y: x + y),[STATS[key]['arr_agemin'] for key in STATS]))
	TOTAL['arr_agemax'] = list(reduce((lambda x,y: x + y),[STATS[key]['arr_agemax'] for key in STATS]))
	TOTAL['arr_age_range'] = list(reduce((lambda x,y: x + y),[STATS[key]['arr_age_range'] for key in STATS]))
	TOTAL['len'] = int(reduce((lambda x,y: x + y),[STATS[key]['len'] for key in STATS]))
	TOTAL['aged_len'] = int(reduce((lambda x,y: x + y),[STATS[key]['aged_len'] for key in STATS]))

	STATS['total'] = TOTAL
	return STATS
STATS = getStats()

categories = ["-legal"]
RES = {}
range = [[17,24],[24,30],[30,36],[36,42],[42,48],[48,54],[54,60],[17,60]]

for i in categories:
	RES[i] = []
agg = 0

print('----------------------------')
arrm = []
#np.seterr(all='raise')
for r in [1]:
	mo = []
	for cat in categories:
		mi= []
		ma = []
		mo = []
		for city in STATS.keys():
			if city != 'total':
				RES[cat] = RES[cat] + c.execute('SELECT * FROM %s WHERE type="%s"' % (city, cat)).fetchall()
		
		
		print(len(RES["-legal"]))
		aged = [[i[5],i[6],i[3]] for i in RES[cat] if (i[5] != 0 or i[6] != 0)]
		print(len(aged))
		minaged = [i[5] for i in RES[cat] if i[5] != 0]
		maxaged = [i[6] for i in RES[cat] if i[6] != 0]
		
		mo = [i[3] for i in RES[cat] if i[3] > 500 and i[3]<200000 and (i[5] != 0 or i[6] != 0)]
		mi += minaged
		ma += maxaged

c.close()
conn.close()