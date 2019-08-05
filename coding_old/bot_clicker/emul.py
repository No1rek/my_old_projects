# -*- coding: utf-8 -*-

import win32api
import win32con
import win32com.client
import win32gui
import win32ui
import time
import sys

from msvcrt import getch
from PIL import Image
from PIL import ImageGrab
#from PyQt4 import QtCore, QtGui, QtWidgets

points = []

shell = win32com.client.Dispatch("WScript.Shell")
shell.SendKeys('%')

COUNTER = 1
ACCURACY = 50

SCREEN_SIZE = [1366, 768]

SLOWER_COEFF = 1



PHONE = ["0982605548"]

NOX_PLAYERS = [];
PLAYER_INTERVAL = [];
PLAYER_STATUS = [];

def load_coordinates_from_file(name):
	global W_WIDTH
	global W_HEIGTH
	ret = []
	f = open(name)
	for line in f:
		if(not '/' in line and not '#' in line):
			x = line.split(',')[0]
			y = line.split(',')[1]
			ret.append({'x': int(x), 'y':int(y)})
		elif(not '/' in line and'#' in line):
			line = line.split('#')[1]
			W_WIDTH = int(line.split(',')[0])
			W_HEIGTH = int(line.split(',')[1])
			
	f.close()
	return ret


def callback(hwnd, extra):
	global SLOWER_COEFF
	global NOX_PLAYERS
	#rect = win32gui.GetWindowRect(hwnd)
	name = win32gui.GetWindowText(hwnd);
	if("NoxPlayer" in name):
		#win32gui.MoveWindow(hwnd, 0, 0, 370, 545, True) # Real size 400x575
		NOX_PLAYERS.append(hwnd)
	#if name == "Nox":
		#win32gui.PostMessage(hwnd,win32con.WM_CLOSE,0,0)

def resize(hwnd, x, y):
	global SLOWER_COEFF
	win32gui.SetForegroundWindow(hwnd)
	rect = win32gui.GetWindowRect(hwnd)
	time.sleep(0.5*SLOWER_COEFF)
	x0 = rect[2] - 2
	y0 = rect[3] - 2
	
	x1 = rect[0] + x
	y1 = rect[1] + y
	
	win32api.SetCursorPos((x0,y0))
	time.sleep(0.5*SLOWER_COEFF)
	win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
	time.sleep(0.5*SLOWER_COEFF)
	win32api.SetCursorPos((x1,y1))
	time.sleep(0.5*SLOWER_COEFF)
	win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
	
	

def get_windows():		
	win32gui.EnumWindows(callback, None);

def click(hwnd,x,y):
	global SLOWER_COEFF
	rect = win32gui.GetWindowRect(hwnd)
	x += rect[0]
	y += rect[1]
	win32api.SetCursorPos((x,y))
	time.sleep(0.1*SLOWER_COEFF)
	win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
	time.sleep(0.1*SLOWER_COEFF)
	win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
	
def pixel(hwnd,x,y):
	global SLOWER_COEFF
	rect = win32gui.GetWindowRect(hwnd)
	
	x += rect[0]
	y += rect[1]
	#hwindc = win32gui.GetWindowDC(hwnd)
	#srcdc = win32ui.CreateDCFromHandle(hwindc)
	#memdc = srcdc.CreateCompatibleDC()
	
	#bmp = win32ui.CreateBitmap()
	
	ret = ImageGrab.grab().load()[x,y]
	return ret
	

	
	#return win32gui.GetPixel(hwnd,x,y)
	

	
#hwnd = win32gui.SetForegroundWindow()
#for i in range(10000):
#	number = str(i)
#	number = "0"*(4 - len(number)) + number		

def main():
	global COUNTER
	global ACCURACY
	global NOX_PLAYERS
	global PLAYER_INTERVAL
	global PLAYER_STATUS
	global SLOWER_COEFF
	global PHONE
	global XY 
	global W_WIDTH
	global W_HEIGTH
	#Значения по умолчанию
	W_WIDTH = 465
	W_HEIGTH = 800
	
	XY = load_coordinates_from_file('coord.txt')	
	
	PHONE_TO_WINDOW_RELEVANCE_ARRAY = []
	
	RGB = (100,0,0)
	
	#получаем окошки
	cut = 0
	get_windows()
	for i in range(len(NOX_PLAYERS)):
		if i >= len(PHONE) - 1:
			cut = i
			break
			
	NOX_PLAYERS = NOX_PLAYERS[0:1]
			
	
	X = 0
	Y = 0
			
	for hwnd in NOX_PLAYERS:
		rect = win32gui.GetWindowRect(hwnd)
		win32gui.MoveWindow(hwnd, 0, 0, rect[2] - rect[0], rect[3] - rect[1], True)
		
		time.sleep(0.2*SLOWER_COEFF)
		resize(hwnd, W_WIDTH, W_HEIGTH)
		
	time.sleep(0.1*SLOWER_COEFF)
	#открываем новую почту и подходим к вводу пароля
		
	#STATUS_ARRAY = [False for i in NOX_PLAYERS]		
	

	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		click(hwnd,XY[0]['x'],XY[0]['y'])
	time.sleep(6*SLOWER_COEFF)
		#Проверяем не вылезло ли говно
	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		check = pixel(hwnd,XY[1]['x'],XY[1]['y'])	#240 770
		if check[0] > 200 and check[1] >200 and check[2] >200 :
			click(hwnd,XY[2]['x'],XY[2]['y'])
				
				
		
		
	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		click(hwnd,XY[3]['x'],XY[3]['y'])
	
	time.sleep(3*SLOWER_COEFF)	
	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		click(hwnd,XY[4]['x'],XY[4]['y'])
		
	time.sleep(3*SLOWER_COEFF)	
	
	#печатаем номер
	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		click(hwnd,XY[5]['x'],XY[5]['y'])
		time.sleep(0.1*SLOWER_COEFF)
		shell.SendKeys(PHONE[NOX_PLAYERS.index(hwnd)])
	time.sleep(2*SLOWER_COEFF)	
	#Телефон
	for hwnd in NOX_PLAYERS:
		win32gui.SetForegroundWindow(hwnd)
		click(hwnd,XY[6]['x'],XY[6]['y'])

	
	time.sleep(3*SLOWER_COEFF)	

	#создаем массив диапазонов	
	for i in range(len(NOX_PLAYERS)):
		PLAYER_INTERVAL.append(0)
		PLAYER_STATUS.append(False)
	#print(PLAYER_INTERVAL)
	
	#перебираем
	while not all(PLAYER_STATUS):
		if(str(win32api.GetAsyncKeyState(ord('Q'))) != "0"):
			print(str(win32api.GetAsyncKeyState(ord('Q'))))
			sys.exit()
		#делаем клик
		for i in range(len(NOX_PLAYERS)):
			if PLAYER_STATUS[i] is False:
				hwnd = NOX_PLAYERS[i]
				iterator = PLAYER_INTERVAL[i]
				
				win32gui.SetForegroundWindow(hwnd)
				click(hwnd,XY[7]['x'],XY[7]['y'])
		time.sleep(0.3*SLOWER_COEFF)
		#производим набор		
		for i in range(len(NOX_PLAYERS)):
			if PLAYER_STATUS[i] is False:
				hwnd = NOX_PLAYERS[i]
				iterator = str(PLAYER_INTERVAL[i])
				win32gui.SetForegroundWindow(hwnd)
		
				shell.SendKeys("{BS}{BS}{BS}{BS}")
				time.sleep(0.2*SLOWER_COEFF)
				shell.SendKeys("0"*(4 - len(iterator)) + iterator)
		time.sleep(0.2*SLOWER_COEFF)
		#Нажимаем подтвердить		
		for i in range(len(NOX_PLAYERS)):
			if PLAYER_STATUS[i] is False:
				hwnd = NOX_PLAYERS[i]
				iterator = PLAYER_INTERVAL[i]
				win32gui.SetForegroundWindow(hwnd)
				
				iterator = PLAYER_INTERVAL[i]				
				click(hwnd,XY[8]['x'],XY[8]['y'])
		time.sleep(1*SLOWER_COEFF)

		for i in range(len(NOX_PLAYERS)):
			if PLAYER_STATUS[i] is False:
				hwnd = NOX_PLAYERS[i]
				iterator = PLAYER_INTERVAL[i]
				if(COUNTER % ACCURACY == 0):
					RGB = pixel(hwnd,XY[9]['x'],XY[9]['y'])
					#print(COUNTER)
					#print(COUNTER % ACCURACY)
					#print(RGB)
					time.sleep(0.5*SLOWER_COEFF)
				#проверяем имеем ли мы темно красный
				if RGB[0] > 90 and RGB[1] < 40 and RGB[2] < 40:
					PLAYER_INTERVAL[i] += 1
					click(hwnd,XY[10]['x'],XY[10]['y'])
					#ERROR
				else:
					PLAYER_STATUS[i] == True
					print(u"Был подобран аккаунт под номером {0}".format(PHONE[i]))
					break
					
		time.sleep(0.5*SLOWER_COEFF)
		COUNTER += 1


if __name__ == '__main__':
	print(u"Введите множитель скорости исполнения( по умолчанию 1 )")
	SLOWER_COEFF = int(raw_input())
	print(u"Введите частоту проверок ввода( по умолчанию 50)")
	ACCURACY = int(raw_input())
	print(u"Введите номера телефонов через ';', например '5235362623;64374373743;745635435345'")
	phones = str(raw_input()).strip()
	
	if ";" in phones:
		PHONE = phones.split(";")
	else:
		PHONE=[phones]
	print(u"Running... Для выхода нажмите Q")
	time.sleep(1)
	main()
		
		
		
		
		
		
		
		
		
			