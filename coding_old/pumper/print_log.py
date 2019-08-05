import matplotlib.pyplot as plt
import json
import time
#from keras import *

#data = json.load(open('pump_log.json'))['Data']

#model = models.load_model('acc95dev5-15sym-0.7.h5')

def get_price(pair, market):
    for p in market:
        if p['Label'] == pair:
            return p

#f = open('new_log.txt', 'r')
data = json.load(open('new_log.txt'))

ECLIPSE = data[0]
SOIL = data[1]

x1 = [float(i['time']) - 1520190000  for i in ECLIPSE]
y11 = [float(i['AskPrice']) for i in ECLIPSE]
y12 = [float(i['BidPrice']) for i in ECLIPSE]
# for i in ECLIPSE:
#     if float(i['time'])

x2 = [float(i['time']) - 1520190000 for i in SOIL]
y21 = [float(i['AskPrice']) for i in SOIL]
y22 = [float(i['BidPrice']) for i in SOIL]


#print(x)
#print(["{:.8f}".format(y) for y in y1])

plt.plot(x1, y11)
plt.plot(x1, y12)
plt.show()

plt.plot(x2, y21)
plt.plot(x2, y22)
plt.show()










# ECLIPSE = []
# SOIL = []
# for l in f:
#     line = json.loads(l)
#     if line['type'] == 'get_markets':
#         ECLIPSE.append({'time':line['time'],
#                         'BidPrice': get_price('EC/BTC', line['result'][0])['BidPrice'],
#                         'AskPrice': get_price('EC/BTC', line['result'][0])['AskPrice']})
#         SOIL.append({'time': line['time'],
#                         'BidPrice': get_price('SOIL/BTC', line['result'][0])['BidPrice'],
#                         'AskPrice': get_price('SOIL/BTC', line['result'][0])['AskPrice']})
#
# DATA = [ECLIPSE, SOIL]
#
# f.close()
# f = open('new_log.txt', 'w')
# json.dump(DATA, f)
# f.close
#
#
# f.close()

