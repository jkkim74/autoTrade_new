import threading
from PyQt5.QtWidgets import *
from kiwoom import *
from datetime import datetime
import FinanceDataReader as fdr
import time
import pickle
import util, jk_util
codes = ['033180','046940']
class Stock(threading.Thread):
    def __init__(self, func, args, name=''):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        self.order_type = 1      #1:매수,2:매도
        threading.Thread.__init__(self, name=name)
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)

    def send_order(self,cnt, code):
        print(cnt)
        account = self.get_account()
        nQty = 1
        if code == '033180':
            stock_price = '10000'
        elif code == '046940':
            stock_price = '5500'
        # 조건검색을 통해 저장한 데이타 가져오기
        print(account, code, stock_price)
        # kiwoom.send_order("send_order", "0101", account, 2, code, nQty, stock_price, "00", "") #매수:1, 매도:2
        # result = kiwoom.order_result
        # if (result == 0):
        #     print("매도주문을 하였습니다.")
        # else:
        #     print("매도 실패하였습니다.")

    def get_account(self):
        account_list = self.kiwoom.get_login_info("ACCNO")
        return account_list.split(';')[0]

def threadTest():
    threads = []
    s_cnt = range(len(codes))
    for i in s_cnt:
        #t = Stock(send_order, (i, codes[i]), send_order.__name__)
        t = threading.Thread(target=Stock.send_order, args=(i, codes[i]))
        threads.append(t)
    for i in s_cnt:
        threads[i].start()
    for i in s_cnt:
        threads[i].join()


if __name__ == '__main__':
    threadTest()
