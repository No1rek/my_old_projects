from keras import *
from keras import *
from keras import *
import math
import random
import decimal
import matplotlib.pyplot as plt
import numpy as np


class DataProcessing:
    # для поиска пампов
    def float_range(self, x, y, jump):
        while x < y:
            yield x
            x = x + jump

    # Нормализует в отрезке 0:1
    def normalize(self, arr):
        if len(arr) == 1:
            return [1]
        arr = np.array(arr)
        min = np.amin(arr)
        # Смещает все значения, чтобы они не были отрицательными
        if min < 0:
            arr = arr - min

        max = np.amax(arr)
        if max != 0:
            arr = arr / max
        return arr

    # Создает шум на графике в пределах отклонения dev
    def make_noise(self, arr, dev, plateau=0.0, leng=0.2, acc=3):
        try:
            # rnd = lambda x: float(random.randint(0, 2 * np.round(np.array([x]), acc)[0] * 10 ** acc)) / 10 ** acc
            rnd = lambda x: float(
                random.randint(-1 * 2 * round(x, acc) * 10 ** acc, 2 * round(x, acc) * 10 ** acc)) / 10 ** acc

            arr = [i + rnd(dev) for i in arr]
            ret = []
            ite = 0
            for i in range(len(arr)):
                ite = len(ret) - 1
                if i < ite:
                    continue
                else:
                    rand = random.randint(0, 1000) / 1000
                    if rand < plateau and i > 0:
                        if round(rand * leng * len(arr)) < (len(arr) - len(ret)):
                            ret = ret + [arr[i] for j in arr[i: i + round(rand * leng * len(arr))]]
                        else:
                            ret = ret + [arr[i] for j in arr[len(ret) + 1:]]
                    else:
                        ret.append(arr[i])
            if len(ret) < len(arr):
                ret = ret + list(arr[len(ret):])
        except Exception as e:
            print('Exception in make_noise: ', e)

        return ret[:len(arr)]

    # Рандомно размещает точки на отрезке от 0 до l с учетом асиметрии для имитации реального пампа
    def make_asym(self, l, asym, scale=1.0):
        arr = []
        for a in range(l):
            rnd = random.randint(0, 100) / 100
            if rnd < abs(asym) and asym != 0:
                if asym > 0:
                    arr.append(scale * (float(random.randint(0, 1000)) / 1000 + 1) / (2 + rnd))
                else:
                    arr.append(scale * (float(random.randint(0, 1000)) / 1000) / (2 + rnd))
            else:
                arr.append(float(random.randint(0, 1000)) / 1000)

        arr = np.array(arr)
        arr = np.sort(arr)
        return arr

    '''
    Генерит график:
    dev_lef - среднее отклонение до вершины, dev_right - отклонение после
    asym - ассиметрия, plateau1,2 - шанс появляться "плато" до и после вершины
    '''

    def generate_parabol_new(self, length, dev_left=0.0, dev_right=0.0, asym=0.0, plateau1=0.0, plateau2=0.0, cut=True):

        peak = {'x': 0, 'y': 0}
        y = lambda x: -1 * x ** 2

        shift = random.randint(0, 100) * asym / 100
        # Делаем параболу
        ax = np.array(list((self.float_range(-1 * length * (1 + shift) / 2, length * (1 - shift) / 2, 1))))
        ay = np.array(list([y(x) for x in ax]))

        # Накладываем смещение
        ay = self.normalize(ay)
        ax = self.make_asym(length, asym)
        ax = self.normalize(ax)
        ax = ax[:min(len(ax), len(ay))]
        ay = ay[:min(len(ax), len(ay))]

        # Берем вершину
        for i in range(len(ay)):
            if ay[i] == np.amax(ay):
                peak['x'] = ax[i]
                peak['y'] = ay[i]
                # Инверсируем опуклость
                # До вершины
                # lin = np.polyfit(ax[:i], ay[:i], 1)
                lin = np.polyfit([0, peak['x']], [0, peak['y']], 1)
                k = peak['y'] / peak['x']
                temp = ay[:i]
                ay[:i] = 2 * (lin[0] * ax[:i] + lin[1])  ##- temp
                # ay[:i] = 2*(k * ax[:i]) - ay[:i]
                # ay[:i] = k * ax[:i]
                # После
                # lin = np.polyfit(ax[i:], ay[i:], 1)
                k = -1 * (peak['y'] / peak['x'])
                lin = np.polyfit([peak['x'], 1], [peak['y'], 0], 1)
                temp = ay[i:]
                ay[i:] = 2 * (lin[0] * ax[i:] + lin[1]) * temp
                # ay[i:] = 2*(k * ax[i:]) - ay[:i]
                # ay[i:] = k * ax[i:] + 2* peak['y'] - ay[i:]

                # Накладываем шум
                ay[:i] = self.make_noise(ay[:i], dev_left, plateau1)
                ay[i:] = self.make_noise(ay[i:], dev_right, plateau2)
                break

        ay = self.normalize(ay)
        ax = self.normalize(ax)

        if cut:
            # Берем новую вершину после наложения шума
            for i in range(len(ay)):
                if ay[i] == np.amax(ay):
                    peak['x'] = ax[i]
                    peak['y'] = ay[i]

                    # Обрезаем
                    n = np.random.choice(list(ax[20:]), 1)
                    if n == 0:
                        n = 0.00000001

                    if peak['x'] > n:
                        peak['x'] *= 1 / n

                        for j in range(len(ay)):
                            if ax[j] == n:
                                peak['y'] = peak['y'] / np.amax(ay[:j])
                                ax = ax[:j]
                                ay = ay[:j]
                                break
                    break

        ax = self.normalize(ax)
        ay = self.normalize(ay)

        try:
            axay = self.align_timeline(ax, ay, length)
        except Exception as e:
            print('Exception in aling_timeline: ', e)
        ax = axay['x']
        ay = axay['y']
        # ay = align_timeline(ax, ay, length)['y']

        ax = np.round(ax, 3)[:length]
        ay = np.round(ay, 3)[:length]

        return {'x': ax, 'y': ay, 'peak': peak}

    '''
    функция превращает массив y, который соответствует равномерному распределению в промежутке от 0 до 1
    например, если x=[0, 0.1, 0.3, 0.7, 1], то функция вернет массив y, такой, чтобы он соответствовал
    распределению [0, 0.25, 0.5, 0.75, 1]
    ищет промежуточные значения с помощью линейных трендов
    нкжно, чтобы массивы были одинаковой длины, x был от 0 до 1, первый элемент был 0
    '''

    def align_timeline(self, ax, ay, length=0):
        ax = np.array(ax)
        ay = np.array(ay)
        ax[0] = 0

        if length == 0:
            length = len(ax)

        if length > len(ax):
            pass

        new_x = np.array(list(self.float_range(0, 1, 1 / (length - 1)))[:length - 1])
        # new_x = np.array(list(self.float_range(0, 1, 1 / (length - 1))))
        new_x = np.concatenate((new_x, [1]))
        new_y = np.array([0.0 for i in range(length)])

        # выравни
        # iterator for old array
        i = 0
        for j in range(length):
            while i < len(ax):
                if new_x[j] == ax[i]:
                    new_y[j] = ay[i]
                    break
                elif new_x[j] > ax[i]:
                    i += 1
                else:
                    # Строим линейный тренд и вычисляем точку
                    k = (ay[i] - ay[i - 1]) / (ax[i] - ax[i - 1])
                    new_y[j] = float(ay[i - 1]) + k * float((new_x[j] - ax[i - 1]))
                    a = 0
                    break
        new_x = np.round(new_x, 3)
        new_y = np.round(new_y, 3)

        return {'x': new_x, 'y': new_y}
