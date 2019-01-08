import sys
from PyQt5.QtWidgets import *
from kiwoom import *
from datetime import datetime
import FinanceDataReader as fdr
import pandas as pd
import time
import pickle

s_year_date = '2019-01-01';
#s_standard_date = '2019-01-04'
#e_standard_date = '2019-01-07'
buy_stock_code = '057030'
total_buy_money = 30000000
maesu_start_time = 184900#90000
maesu_end_time  = 185100#93000
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

    def get_cur_price(self, code):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
        return self.kiwoom.cur_price

    def get_prev_date(self):
        # 금일날짜
        today = datetime.today().strftime("%Y%m%d")
        # 영업일 하루전날짜
        df_hdays = pd.read_excel("data.xls")
        hdays = df_hdays['일자 및 요일'].str.extract('(\d{4}-\d{2}-\d{2})', expand=False)
        hdays = pd.to_datetime(hdays)
        hdays.name = '날짜'
        mdays = pd.date_range('2019-01-01', '2019-12-31', freq='B')
        #print(mdays)
        mdays = mdays.drop(hdays)
        #f_mdays = mdays.to_frame(index=True)
        #print(f_mdays)
        # 개장일을 index로 갖는 DataFrame
        #data = {'values': range(1, 31)}
        #df_sample = pd.DataFrame(data, index=pd.date_range('2019-01-01', '2019-01-31'))
        df_mdays = pd.DataFrame({'date':mdays})
        df_mdays_list = df_mdays['date'].tolist()
        for i, df_day in enumerate(df_mdays_list):
            if(df_day.__format__('%Y%m%d') == today):
                self.prev_bus_day_1 = df_mdays_list[i - 1].__format__('%Y-%m-%d')
                self.prev_bus_day_2 = df_mdays_list[i - 2].__format__('%Y-%m-%d')

    def run(self):
        account = self.get_account()
        # 금일날짜
        today   = datetime.today().strftime("%Y-%m-%d")
        today_f = datetime.today().strftime("%Y%m%d")
        self.get_prev_date()
        #data = self.load_data()
        #codes = [x[0] for x in data]
        #print(data)
        #print(codes)
        s_standard_date = self.prev_bus_day_2
        e_standard_date = self.prev_bus_day_1
        print('5%이상상승당일 : ', s_standard_date, '시가갭날짜 : ', e_standard_date)
        # 대상종목의 매수가 산정을 위한 가격데이타 수집
        df = fdr.DataReader(buy_stock_code, s_year_date)
        print('5%이상상승당일 종가 : ', df['Close'][s_standard_date])  # 5%이상상승당일 종가
        print('시가갭날 시가 : ', df['Open'][e_standard_date])  # 매수전날 시가
        print('시가갭날 종가 : ', df['Close'][e_standard_date])  # 매수전날 종가

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
        print("시작가:", self.s_buy_price, ", 종료가:", self.e_buy_price, ", 당일시작가:", self.d_open_price)
        # 금일 시작가가 매수구간의 시작가보다 작으면 매수금지
        if(self.s_buy_price > self.d_open_price):
            raise Exception("Can't Buy Stock")
        result = -1
        while True:
            now_time = int(datetime.now().strftime('%H%M%S'))
            self.d_cur_price = int(self.get_cur_price(buy_stock_code)[1:])
            print('현재시간 : ', now_time,'현재가 : ', self.d_cur_price )
            if(maesu_end_time >= now_time >= maesu_start_time):
                if((self.e_buy_price >= self.d_cur_price  >=  self.s_buy_price) and result == -1):
                    high_price = int(self.get_high(buy_stock_code)[1:])
                    nQty = int(total_buy_money / high_price)
                    print(high_price, nQty)
                    result = self.kiwoom.send_order("send_order", "0101", account, 1, buy_stock_code, nQty, high_price, "03", "")
                    print(result)
                    if(result == 0):
                        print("매수주문을 하였습니다.")
                        break
                    else:
                        print("매수주문을 실패하였습니다.")
                        break
            else:
                break
            time.sleep(0.2)


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