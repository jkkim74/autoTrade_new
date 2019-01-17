from kiwoom import *
from PyQt5.QtWidgets import *
import threading
codes = ['033180','046940']
class Stock(threading.Thread):
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()
        threading.Thread.__init__(self)

    def run(self):
        print("======== Stock ==========")
        for i in range(len(codes)):
            self.send_order(i, codes[i])

    def send_order(self,cnt, code):
        account = self.get_account()
        nQty = 1
        if code == '033180':
            stock_price = '10000'
        elif code == '046940':
            stock_price = '5500'
        # 조건검색을 통해 저장한 데이타 가져오기
        print(cnt, account, code, stock_price)
        self.kiwoom.send_order("send_order", "0101", account, 2, code, nQty, stock_price, "00", "") #매수:1, 매도:2
        result = self.kiwoom.order_result
        if (result == 0):
            print("매도주문을 하였습니다.")
        else:
            print("매도 실패하였습니다.")
        # t = threading.Thread(target=self.kiwoom.send_order, args=("send_order", "0101", account, 2, code, nQty, stock_price, "00", ""))
        # t.start()
        # t.join()

    def get_account(self):
        account_list = self.kiwoom.get_login_info("ACCNO")
        return account_list.split(';')[0]

app = QApplication(sys.argv)
stock = Stock()
stock.run()