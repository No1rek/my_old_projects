# -*- coding: utf-8 -*-

import requests
import re
import lxml.html as html
import cssselect
import sqlite3
import time

from functools import reduce

#Подключение к базе
conn = sqlite3.connect('result.db')
#Создание курсора
c = conn.cursor()
#Проверяем наличие ключевых слов
def check(l):
	l = l.lower()
	l = re.split(r"[\.,;]",l)
	A = r"график|ставк|режим|рабо|утра|вечер|смен|опыт|час|ч\.|дн|плат|заробіт|плат|прац|доход|з.п|зп|грн|у.е.|компан|рын|[a-z]|символ|знак|тыс|сот|тел|літ|\%"
	B = r"возраст|вік|жінк|мужч|женщ|люд|парн|девушк|особ|лиц"
	for x in l:
		if re.search(r"[Зз]арплат|[Ww]ag|[Оо]клад|[Зз]\.[Пп]|[Сс]тавк|[Пп]латн", x):
			#assert False, "test"
			substr = re.search(r"[Зз]арплат|[Ww]ag|[Оо]клад|[Зз]\.[Пп]|[Сс]тавк|[Пп]латн", x).group(0)
			if re.search(r"[0-9]{4,}", x[x.index(substr):]):
				x = "W "+re.search(r"[0-9]{4,}", x[x.index(substr):]).group(0)
			return x #and re.search(r"лет|рок|чолов|жінк|мужч|женщ|люд|парн|девушк|особ|лиц", x)
		elif len(re.findall(r"[0-9]{2,}", x)) in [1,2]  and (not re.search(A, x) or re.search(B,x)):
			if all([(lambda y: int(y)>17 and int(y)<60)(i) for i in re.findall(r"[0-9]{2,}", x)]):
				numb = [int(i) for i in re.findall(r"[0-9]{2,}", x)]
				#print("dd",numb)
				#numb = filter(lambda x: x>17 and x<60, numb)
				numb = sorted(numb)
				#print(numb)
				if len(numb)>1:
					numb = "-".join([str(i) for i in numb[0:2]])
				else:
					numb = numb[0]
				return "A "+str(numb)
			else:
				return ""
		elif re.search(r"высш[\w]{0,2} [^\.,; ]*[\s]?образов|вищ[\w]{0,2} [^\.,; ]*[\s]?освіт", x):
			return "E "
		else:
			return ""

#Заполняем массив конечным результатом		
def fulfil(var, arr):
	for i in arr:
		beginning = i[0:2]
		if "W " == beginning:
			try:
				var["wage"] = int(i[2:])
			except:
				var["wage"] = 0
		elif "A " == beginning: 
			age = i[2:]
			if len(age) == 5:
				try:
					var["agemin"] = int(age[0:2])
					var["agemax"] = int(age[3:])
				except:
					var["agemin"] = 0
					var["agemax"] = 0
			elif len(age) == 2:
				try:
					age = int(age)
					if age < 30:
						var["agemin"] = age
					else:
						var["agemax"] = age
				except:
					var["agemin"] = 0
					var["agemax"] = 0
			else:
				print('zerozero')
				var["agemin"] = 0
				var["agemax"] = 0
		elif "E " == beginning: 
			var['education'] = 1
			
		return var
#Пытаемся подключиться пока не выйдет		
def retryGetUntilItWorks(url):
	while True:
		try:
			ret = requests.get(url)
			break
		except:
			time.sleep(2)
			continue
	return ret
categories = ["-it","-administration","-accounting","-hotel-restaurant-tourism","-design-art","-beauty-sports","-culture-music-showbiz","-logistic-supply-chain","-marketing-advertising-pr","-healthcare","-real-estate","-education-scientific","-security","-sales","-production-engineering","-retail","-office-secretarial","-agriculture","-publishing-media","-insurance","-construction-architecture","-customer-service","-telecommunications","-management-executive","-transport","-hr-recruitment","-banking-finance","-legal"]
domain = "https://www.work.ua"

cities = ['-kv','-kh','-od','-dp','-zp','-lv','-nk','-vn','-zt']
#Счетчик для вывода
counter = 0

#Массив для работы с БД
result = []

i = input("Введите номер годода от 0 до 8: -kv','-kh','-od','-dp','-zp','-lv','-nk','-vn','-zt")
cities = [cities[int(i)]]

#-Листать города------------------------------
for city in cities:	
#--Листать категории--------------------------
	for cat in categories:
		if(len(list(c.execute("SELECT * FROM %s WHERE type='%s';" % (city[1:], cat))))):
			continue
			
		url = domain + "/jobs{0}{1}".format(city,cat)
		tree = html.fromstring(retryGetUntilItWorks(url).text)
		if len(tree.cssselect('ul.pagination.hidden-xs')):
			pagecount = int(tree.cssselect('ul.pagination.hidden-xs  li:nth-last-child(2) a')[0].text)
		else:
			pagecount = 1
		
		#--Листать страницы---------------------------
		for ind2 in range(pagecount):
			url = domain + "/jobs{0}{1}/?page={2}".format(city,cat,str(ind2+1))
			tree = html.fromstring(retryGetUntilItWorks(url).text)
			posts = tree.cssselect("div.card.card-hover.card-visited.job-link.card-logotype")
			
			#--Листать посты--------------------------
			for i in posts:
				result.append({"type":"","wage":0, "link":"", "agemin":0, "agemax":0, "needcheck":0, "text":[], "education":0})
				result[-1]["type"] = cat
				
				result[-1]["link"] = i.cssselect(".job-link h2 a")[0].attrib['href']
				posturl = domain + result[-1]["link"]
				
				post = html.fromstring(requests.get(posturl).text)
				if post.cssselect("div.card h3.wordwrap b"):			
					result[-1]["wage"] = re.search(r"[0-9]*", post.cssselect("div.card h3.wordwrap b")[0].text).group(0)

				res = [check(i.text) for i in post.cssselect(".overflow.wordwrap *") if type(i.text) == str]
				res = list(filter(lambda x: len(x)>0,res))
				if len(res) > 2 and not "E" in res:
					result[-1]["needcheck"] = 1
					result[-1]["text"] = res
				elif len(res) > 0:
					result[-1] = fulfil(result[-1], res)
					result[-1]["text"] = res
				print("city: {0};category: {1}; page: {2}; post: {3}, total: {4}".format(city, cat, str(ind2+1), posts.index(i), str(counter)))
				print(result[-1])
				
				counter+=1
	for r in result:
		#Наполнение таблицы
		c.execute("INSERT INTO %s (city, type, wage, link, agemin, agemax, education) VALUES ('%s','%s','%s','%s','%s','%s','%s')" % (city[1:],city, r['type'], r['wage'], r['link'], r['agemin'], r['agemax'], r['education']))
		#Подтверждение отправки данных в базу
		conn.commit()
	result = []

#Завершение соединения
c.close()
conn.close()
print('FINISH')
input("\n\nНажмите Enter чтобы выйти .")
