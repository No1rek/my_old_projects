# -*- coding: utf-8 -*-
import socket
import time
import datetime
import json
import re
import sqlite3

def dataFind(data, keyword):
	if(data == ""):
		return ""

	pat = keyword+r'.*[\s]'
	data = re.search(pat,data).group(0)
	pat = keyword+r': |[\s]'
	data = re.sub(pat,'',data)
	return data

def data_start_reg_func(email, passw, proxy):		
	conn = sqlite3.connect('db.db')
	c = conn.cursor()
	#Выбрать id, имя, карту, отель, дату, реферальную ссылку		
	reff = min([ i[2] for i in c.execute('SELECT * FROM reffs').fetchall()])	
	if(reff and reff > 9):	
		return "error: no free reffs".encode('utf8')
	reff = c.execute("SELECT * FROM reffs WHERE times_used='{0}'".format(reff)).fetchall()[0]
	reffid = reff[0]
	reff = reff[1]
				
	#-----
	name = c.execute('SELECT * FROM names WHERE used=0').fetchall()[0]
	if(not name):
		return "error: no free names".encode('utf8')
	nameid = name[0]
	name = name[1]
		
		#-----
	try:
		card = min([ i[2] for i in c.execute('SELECT * FROM cards').fetchall()])	
	except:
		return "error: no free cards".encode('utf8')
		
	card = c.execute("SELECT * FROM cards WHERE times_used='{0}'".format(card)).fetchall()[0]
	cardid = card[0]
	card = card[1]
	cardholder = card[3]
		
	#-----Разбираемся с датами
	
	#определяем ближайшую свободную дату yyyy-mm-dd
	host = c.execute('SELECT * FROM hostels').fetchall()
	daysto = lambda x: str(datetime.date(int(x[3].split('-')[0]),int(x[3].split('-')[1]),int(x[3].split('-')[2])) - datetime.date.today()).split(' ')[0]
	dates = [[int(daysto(i)),i[0]]  for i in host]
	date = 9999
	hostid = None
	for i in dates:
		if date > i[0]:
			hostid = i[1]
			date = i[0]
			
	host = c.execute('SELECT * FROM hostels WHERE id="{0}"'.format(hostid)).fetchall()[0]
	if(not host or not hostid):
		return "error: no hosts".encode('utf8')
			
	arrival = host[3]
	#если дата устарела выбираем завтрашний день
	arr_year = int(arrival.split('-')[0])
	arr_month = int(arrival.split('-')[1])
	arr_day = int(arrival.split('-')[2])
	
	tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
	
	if(arr_year < tomorrow.year):
		arrival = tomorrow.strftime("%Y-%m-%d")
	elif(arr_year == tomorrow.year):
		if(arr_month< tomorrow.month):
			arrival = tomorrow.strftime("%Y-%m-%d")
		elif(arr_month == tomorrow.month):
			if(arr_day < tomorrow.day):
				arrival = tomorrow.strftime("%Y-%m-%d")
				

	
	arr_year = int(arrival.split('-')[0])
	arr_month = int(arrival.split('-')[1])
	arr_day = int(arrival.split('-')[2])
	
	
	host = host[1]
	#определяем дату отбытия
	departure = "-".join(str(datetime.date(arr_year,  arr_month , arr_day ) + datetime.timedelta(days=1)).split(' '))
		

	#-----Пишем данные в БД
	
	c.execute("INSERT INTO Users(name, pass, mail, number, card, arrival, objlink, reff, reff_status, reg_status, arr_host_visited_id, proxy_used) VALUES ({0})".format('"'+'","'.join([name, passw, email, "", card, arrival, host, reff, "no referal", "registered", "[]", proxy])+'"'))
	conn.commit()
	#Добавляем количество использований реферала
	value = c.execute("SELECT * FROM reffs WHERE reff='{0}'".format(reff)).fetchall()[0][2]
	value += 1
	c.execute("UPDATE reffs SET times_used = {0} WHERE reff='{1}'".format(value,reff))
	conn.commit()	
	#Добавляем количество использований карты
	value = c.execute("SELECT * FROM cards WHERE card='{0}'".format(card)).fetchall()[0][2]
	value += 1
	c.execute("UPDATE cards SET times_used = {0} WHERE card='{1}'".format(value,card))
	conn.commit()
	#Изменяем свободную дату хостела
	c.execute("UPDATE hostels SET open_date = {0} WHERE link='{1}'".format(departure,host))
	conn.commit()

	
	#--Формируем данные для отправки
	data_return = ",".join([name, passw, email, card, arrival, departure, host, reff, cardholder])
	#--Закрываем БД
	c.close()
	conn.close()
	return data_return
def data_registration_successful_func(passw, used_reff, new_reff):	
	#Изменяем статус пользователя
	c.execute("UPDATE Users SET reg_status = {0} WHERE pass='{1}'".format("booked", passw))
	conn.commit()
	
	#Добавляем количество использований списка посещенных хостелов
	
	#Добавляем новый реферал
	c.execute("INSERT INTO reffs(reff, times_used) VALUES ({0},0)".format(new_reff))
	conn.commit()
	
	
	
def MAIN(data):
	data = data.decode()
	if(data==""):
		return "error occured".encode('utf8')
	#Определяем что нам прислали
	status = dataFind(data, 'stat')
	
	
	if status == 'start_reg':
		email = dataFind(data, 'email')
		passw = dataFind(data, 'passw')
		proxy = dataFind(data, 'proxy')
		data_return = data_start_reg_func(email, passw, proxy)
		
	if status == 'booking_succesful':
		passw = dataFind(data, 'passw')
		used_reff = dataFind(data, 'used_reff')
		new_reff = dataFind(data, 'new_reff')
		data_return = data_start_reg_func(passw, used_reff, new_reff)
		
		
	if(data_return==""):
		data_return = "error occured" + str(data_return)
	return str(data_return).encode('utf8')

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 9090))
serversocket.listen(5)
print('Server is waiting for connections.')
while True:
	conn, addr = serversocket.accept()
	print('Connection:', addr)
	data = conn.recv(1024)
	print('=-=',data)
	if not data:
		continue
	print('------------------------------')
	#print(MAIN(data))
	print('------------------------------')
	hdrs = 'HTTP/1.1\r\nServer: nginx\r\nContent-Type: text/html\r\nConnection: keep-alive\r\nKeep-Alive: timeout=25\r\nData: {0}\r\n\r\n<html><head></head><body></body></html>'.format(MAIN(data)).encode('utf8')
	conn.send(hdrs)
	print(hdrs)
	conn.close()
	# Делаем задержку, чтобы цикл не сильно загружал процессор
	time.sleep(0.1)
