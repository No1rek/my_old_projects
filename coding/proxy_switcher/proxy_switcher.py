from utils.singleton import singleton
import os
import time

@singleton
class ProxySwitcher():
    def __init__(self):
        self.requests_to_switch = 500
        self.proxy_list = [""]
        self.requests_made = 0
        self.switch_callback = None
        self.proxy_iterator = 0

    def configure(self, proxy_list=None, requests_to_switch=500, switch_callback=None):
        proxy_list.append("")
        self.requests_to_switch = requests_to_switch
        self.proxy_list = proxy_list
        self.requests_made = 0
        self.switch_callback = switch_callback
        self.proxy_iterator = proxy_list.index("")

    def switch(self):
        self.requests_made, nullified = self._increase_or_nullify(self.requests_made, self.requests_to_switch)
        self.proxy_iterator, _ = self._increase_or_nullify(self.proxy_iterator, len(self.proxy_list) - 1)
        if nullified:
            self.requests_made = 0
            os.environ["https_proxy"] = self.proxy_list[self.proxy_iterator]
            if self.switch_callback is not None:
                self.switch_callback(self.proxy_list[self.proxy_iterator], time.time())

    def switch_now(self):
        self.proxy_iterator, _ = self._increase_or_nullify(self.proxy_iterator, len(self.proxy_list)-1)
        self.requests_made = 0
        os.environ["https_proxy"] = self.proxy_list[self.proxy_iterator]
        if self.switch_callback is not None:
            self.switch_callback(self.proxy_list[self.proxy_iterator], time.time())

    def _increase_or_nullify(self, number, limit):
        if number + 1 > limit:
            nullified = True
            return 0, nullified
        else:
            nullified = False
            return number + 1, nullified

