# test5.py
import threading
import time
from kiwoom import *
from datetime import datetime

class PyTrader(threading.Thread):
    def __init__(self, code):
        threading.Thread.__init__(self)
        # self.kiwoom = Kiwoom()
        # self.kiwoom.comm_connect()
        self.code = code
        self.name = threading.currentThread().getName()

    def get_start_price(self, code, s_date):
        # self.kiwoom.set_input_value("종목코드", code)
        # self.kiwoom.set_input_value("시작일자", s_date)
        # self.kiwoom.comm_rq_data("opt10086_req", "opt10086", 0, "0101")

        return "+6000"

    def run(self):
        self.sendOrder(self.code)

    def sendOrder(self,buy_stock_code):
        today_f = datetime.today().strftime("%Y%m%d")
        while True:
            # 금일 시가 조회
            self.d_open_price = self.get_start_price(buy_stock_code, today_f)
            if (self.d_open_price[0] == '-' or self.d_open_price[0] == '+'):
                self.d_open_price = self.d_open_price[1:]
            self.d_open_price = int(self.d_open_price)
            print("시작가 ==>", self.d_open_price,"thread name=>",self.name)

            time.sleep(2)

stock_list = ['126880','006890']
threads = []
for stock in stock_list:
    pymon = PyTrader(stock)
    threads.append(pymon)

for thread in threads:
    thread.daemon = True
    thread.start()
    time.sleep(1)

for thread in threads:
    thread.join()
    time.sleep(1)
