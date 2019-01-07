import sys
from PyQt5.QtWidgets import *
from kiwoom import *
from datetime import datetime
import FinanceDataReader as fdr
import pickle

s_year_date = '2019-01-01';
s_standard_date = '2019-01-04'
e_standard_date = '2019-01-07'
buy_stock_code = '057030'
total_buy_money = 30000000
class PyTrader:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def get_account(self):
        account_list = self.kiwoom.get_login_info("ACCNO")
        return account_list.split(';')[0]

    def get_start_price(self, code, s_date):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("시작일자", s_date)
        self.kiwoom.comm_rq_data("opt10086_req", "opt10086", 0, "0101")
        return self.kiwoom.s_price

    def get_high(self, code):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
        return self.kiwoom.high

    def run(self):
        account = self.get_account()
        # 금일날짜
        today   = datetime.today().strftime("%Y-%m-%d")
        today_f = datetime.today().strftime("%Y%m%d")

        #data = self.load_data()
        #codes = [x[0] for x in data]
        #print(data)
        #print(codes)

        # 대상종목의 매수가 산정을 위한 가격데이타 수집
        df = fdr.DataReader(buy_stock_code, s_year_date)
        print(df['Close'][s_standard_date])  # 5%이상상승당일 종가
        print(df['Open'][e_standard_date])  # 매수전날 시가
        print(df['Close'][e_standard_date])  # 매수전날 종가

        # 매수가능 구간 가격 조회
        s_buy_close_price_t = df['Close'][s_standard_date]
        e_buy_open_price_t = df['Open'][e_standard_date]
        e_buy_close_price_t = df['Close'][e_standard_date]
        if (e_buy_open_price_t > e_buy_close_price_t):
            self.e_buy_price = int(e_buy_close_price_t)
        else:
            self.e_buy_price = int(e_buy_open_price_t)

        if (s_buy_close_price_t > self.e_buy_price):
            self.s_buy_price = int(self.e_buy_price)
            self.e_buy_price = int(s_buy_close_price_t)
        else:
            self.s_buy_price = int(s_buy_close_price_t)
            self.e_buy_price = int(self.e_buy_price)

        # 금일 시가 조회
        self.d_open_price = int(self.get_start_price(buy_stock_code, today_f)[1:])
        # self.e_buy_price = 4050
        print(self.s_buy_price)
        print(self.e_buy_price)
        print(self.d_open_price)

        if(self.e_buy_price >= self.d_open_price  >=  self.s_buy_price):
            high_price = int(self.get_high(buy_stock_code)[1:])
            nQty = int(total_buy_money / high_price)
            print(high_price, nQty)
            result = self.kiwoom.send_order("send_order", "0101", account, 1, buy_stock_code, nQty, high_price, "03", "")
            print(result)

        #매수
        #for code in codes:
        #    self.kiwoom.send_order("send_order", "0101", account, 1, code, 10, 0, "03", "")
        #    print(code)

    def load_data(self):
        try:
            f = open("./database.db", "rb")
            data = pickle.load(f)
            f.close()
            return data
        except:
            pass

app = QApplication(sys.argv)
pymon = PyTrader()
pymon.run()