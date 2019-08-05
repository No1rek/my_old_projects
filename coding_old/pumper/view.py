import sys, linecache, os
import tkinter as tk
from tkinter.ttk import Style
import threading
import time
import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def test(Form):
    for i in range(11515):
        X = np.linspace(0+i, 2 * np.pi+i, 50)
        Y = np.sin(X)
        Form.plot(X, Y)
        time.sleep(0.5)


class Form():
    def __init__(self, Bot=None, INDICATORS=[]):
        self.BOT = Bot
        self.tk = tk

        self.root = tk.Tk()
        self.root.style = Style()
        self.root.style.theme_use('alt')
        self.root.title('Пампер')
        self.root.geometry('950x740+100+100')
        self.root.resizable(False, False)

        self.bp = tk.StringVar()
        self.cp = tk.StringVar()

        # Лого

        # Кнопка старт
        self.bstart = tk.Button(text='Start', command=self.BOT.run, bg="#A5E1A5", bd=0)
        self.bstart.place(height=32, width=100, x=540, y=42)
        # self.bstart.grid(row=0, column=0)

        # Кнопка продать
        self.bsell = tk.Button(text='Sell', command=self.BOT.force_sell, bg="#E0FB68", bd=0)
        self.bsell.place(height=32, width=100, x=655 , y=42)
        # self.bsell.grid(row=0, column=1)

        # Цена покупки
        self.buy_price_capt = tk.Label(text="Цена покупки: ")
        self.buy_price_capt.place(x=210, y=15)
        self.buy_price = tk.Label(textvariable=self.bp)
        self.buy_price.place(x=350 , y=15)

        # Текущая цена
        self.current_price_capt = tk.Label(text="Текущая цена: ")
        self.current_price_capt.place(x=210, y=45)
        self.current_price = tk.Label(textvariable=self.cp)
        self.current_price.place(x=350 , y=45)

        # Прибыль

        # # Галочка продажа вручную
        # self.manual_caption = tk.Label(text="Automatic sell")
        # self.manual_caption.grid(row=0, column=2)
        # self.manual = tk.Checkbutton(variable=self.BOT.manual_sell, onvalue=True, offvalue=False)
        # self.manual.grid(row=0, column=3)

        # Фрейм для виджетов
        self.widgetpanel = tk.Frame(self.root, bg="#C3CFD9")
        self.widgetpanel.place(height=555, width=165, x=775 , y=15)
        self.widgets = []

        for indx, var in enumerate(INDICATORS):
            newFrame = tk.Frame(self.widgetpanel, bd=2)
            self.widgets.append(newFrame)
            self.widgets[-1].grid(row=indx)

            name = 'Widget '+str(indx)
            wgcontents = tk.Frame(self.widgets[-1])
            trigger = False
            try:
                name = var.name
            except:
                pass
            try:
                wgcontents = var.view(self.widgets[-1])
            except:
                pass
            try:
                trigger = var.enabled
            except:
                pass
            wgname = tk.Label(self.widgets[-1], text=name, )
            wgname.grid(row=0, sticky=tk.W+tk.E)
            wgcontents.grid(row=1, rowspan=3, sticky=tk.W+tk.E)
            triggercaption = tk.Label(self.widgets[-1], text="Enabled ")
            triggercaption.grid(row=4, column=0, columnspan=3, sticky=tk.W+tk.E)
            triggerbtn = tk.Checkbutton(self.widgets[-1], variable=trigger, onvalue=True, offvalue=False)
            triggerbtn.grid(row=4, column=3, sticky=tk.W+tk.E)






        # Главный график
        self.figure_main = Figure(figsize=(9, 3)) #
        self.figure_main.tight_layout()
        # self.figure_main.text(fontsize=12)
        self.graph_frame = tk.Frame(self.root,  bg="#C3CFD9")
        self.graph_frame.place(height=300, width=750, x=10 , y=80)
        self.canvas = FigureCanvasTkAgg(self.figure_main, master=self.graph_frame)
        self.canvas.get_tk_widget().pack() # relheight=1.0, relwidth=1.0
        # self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=2)

        # Глубина рынка
        self.figure_orders = Figure(figsize=(9,2)) #
        self.figure_orders.tight_layout()
        #self.figure_orders.text(0,0,0, fontsize=8)
        self.orders_frame = tk.Frame(self.root,  bg="#C3CFD9")
        self.orders_frame.place(height=180, width=750, x=10, y=390)
        self.canvas = FigureCanvasTkAgg(self.figure_orders, master=self.orders_frame)
        self.canvas.get_tk_widget().pack()

        # Оценочная величина пампа

        # Лог
        # self.Log = tk.Frame(self.root,  bg="#C3CFD9")
        # self.Log.place(height=150, width=930, x=10, y=580)
        self.Log = tk.Listbox(self.root, bg="#C3CFD9")
        self.Log.place(height=150, width=930, x=10, y=580)

        # self.plot(X,Y,self.root)

        self.update_captions()

    def update_captions(self):
        self.bp.set("{:.8f}".format(self.BOT.buying_price))
        try:
            profit = (self.BOT.current_price/self.BOT.buying_price-1)*100
        except:
            profit = 0
        self.cp.set("{:.8f}   Profit:   {:.1f} %".format(self.BOT.current_price, profit))
        return

    def plot_orders(self):
        try:
            if len(self.BOT.orders) > 0:
                orders = self.BOT.orders
                start_price = self.BOT.start_price
                current_price = self.BOT.current_price
                sell_orders = orders['Sell']#[::-1]

                X = [round(ord['Price']/start_price,1) for ord in sell_orders]
                Y = []
                X1 = float(current_price / start_price)
                cumulative = 0
                for ord in sell_orders:
                    Y.append(round(ord['Total'] + cumulative,2))
                    cumulative += ord['Total']

                for i in range(len(X) - 1):
                    if X1 >= X[i] and X1 < X[i+1]:
                        Y1 = Y[i]
                        break
                else:
                    Y1 = Y[0]

                X1 = current_price/start_price
            else:
                X = [0, 0]
                Y = [0, 0]
                X1 = [0]
                Y1 = [0]

            self.figure_orders.clear()
            a = self.figure_orders.add_subplot(111)
            a.plot(X, Y, color='red')
            a.plot(X1,Y1,'ro')
            self.figure_orders.canvas.draw()

        except:
            PrintException()



        return

    def plot(self):
        self.update_captions()
        self.plot_orders()

        history = self.BOT.history
        master = self.root
        currency = self.BOT.currency
        if len(currency) > 0:
            X = []
            AY = []
            BY = []
            for i in range(len(history)):
                price = self.BOT.get_price(currency + '/BTC', i, data=history)
                X.append(float(history[i]['time']) - float(self.BOT.history[self.BOT.pump_start_id]['time']))
                AY.append(float(price['AskPrice']))
                BY.append(float(price['BidPrice']))
        else:
            X = [0,0]
            AY = [0,0]
            BY = [0,0]

        self.figure_main.clear()
        a = self.figure_main.add_subplot(111)
        a.plot(X, AY, color='green')
        a.plot(X, BY, color='red')
        self.figure_main.canvas.draw()


        # a.set_title ("Estimation Grid", fontsize=16)
        # a.set_ylabel("Y", fontsize=14)
        # a.set_xlabel("X", fontsize=14)

        self.canvas.draw()

    def show(self):
        self.root.mainloop()

# if __name__ == '__main__':
#     F = Form()
#     F.show()