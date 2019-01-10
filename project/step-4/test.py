import sys
from PyQt5.QtWidgets import *

class Test:
    def run(self):
        price = self._get_maedo_price(99320)
        print(price)

    def _get_maedo_price(self, price):
        s_price = int(price * 1.02)
        if (1000 <= s_price < 5000):
            r_price = round(s_price, -1)
        elif (5000 <= s_price < 10000):
            r_price = round(s_price, -1)
        elif (10000 <= s_price < 50000):
            r_price = round(s_price, -2)
        elif (50000 <= s_price < 100000):
            r_price = round(s_price, -2)
        elif (100000 <= s_price < 500000):
            dif = s_price % 500
            r_price = s_price - dif
        elif (s_price >= 500000):
            r_price = round(s_price, -3)
        else:
            r_price = s_price
        return r_price


app = QApplication(sys.argv)
test = Test()
test.run()