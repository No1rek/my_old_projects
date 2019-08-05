from keras.models import load_model
import numpy as np
import time

def load_var(var, n, section='settings'):
    global config
    try:
        value = config[section][n]
        if str(value).lower() == 'true' \
                or str(value).lower() == 'false':
            return bool(str(value).lower() == 'true')
        return type(var)(value)
    except KeyError:
        return var

class NeuralNetwork(object):
    def __init__(self, BOT):

        self.BOT = BOT
        # Чувствительность сети
        self.accuracy = 0.1
        self.name = 'NeuralNetwork'
        self.enabled = False

        from keras import backend as K
        import tensorflow as tf
        K.clear_session()
        sess = tf.Session()
        K.set_session(sess)

        self.model = load_model('model.h5')
        self.model_inputs = 256
        self.wait_till_pump_raise = 60  # Секунд

    def __call__(self, *args, **kwargs):
        time_passed = time.time() - float(self.BOT.history[self.BOT.pump_start_id]['time'])
        # print('NN: ', time_passed)

        if time_passed > self.wait_till_pump_raise:
            history = self.BOT.history[max(self.BOT.pump_start_id, 0):]
            time_start = float(self.BOT.history[max(self.BOT.pump_start_id, 0)]['time'])
            ay = [float(self.BOT.get_price(self.BOT.currency + '/BTC', i)['AskPrice']) for i in range(len(history))]
            ax = [float(i['time']) - time_start for i in history]
            ax = self.BOT.data_processing.normalize(ax)
            ay = self.BOT.data_processing.normalize(ay)
            inputs = self.BOT.data_processing.align_timeline(ax, ay, self.model_inputs)['y']

            inputs = np.array([np.array(self.BOT.data_processing.normalize(inputs))])

            result = self.model.predict(inputs)

            if result[0][1] - result[0][1] >= self.accuracy:
            #if round(result[0][1]) == 1 and round(result[0][0]) == 0:
                print('NN: ', 1)
                return 1
            else:
                print('NN: ', -1)
                return -1
        print('NN: ', 0)
        return 0

    def destructor(self):
        del self.model
        del self



class Ladder(object):
    def __init__(self, BOT):
        self.BOT = BOT
        self.name = 'Ladder'
        self.enabled = False

        self.wait_till_pump_raise = 60  # Секунд, до этого момента лесенка строиться не будет, по окончанию self.ladder_enable=True
        self.ladder_enabled = False
        self.ladder = [15, 25, 50, 100, 150, 200, 250, 300, 500] # Последний элемент -продает сразу
        self.ladder_activated = list([False for i in self.ladder])
        self.decision_delay = 5.0  # Задержка секунд между проверками графика

    def __call__(self, *args, **kwargs):
        time_passed = time.time() - float(self.BOT.history[self.BOT.pump_start_id]['time'])
        # print('Ladder: ', time_passed)
        price = float(self.BOT.get_price(self.BOT.currency + '/BTC')['AskPrice'])
        start_price = float(self.BOT.get_price(self.BOT.currency + '/BTC', self.BOT.pump_start_id)['AskPrice'])
        price_difference = (price/start_price - 1)*100
        if time_passed > self.wait_till_pump_raise:
            for i in range(len(self.ladder)):
                if price_difference < self.ladder[i] and self.ladder_activated:
                    print('Ladder: ', 2)
                    return 2
                elif i > 0 and price_difference >= self.ladder[i]:
                    print('Ladder: ', 1)
                    self.ladder_activated[i - 1] = True
                elif price_difference >= self.ladder[-1]:
                    print('Ladder: ', 3)
                    return 3
        print('Ladder: ', 0)
        return 0



