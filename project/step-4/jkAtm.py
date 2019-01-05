import sys
from PyQt5.QtWidgets import *
import FinanceDataReader as fdr
from datetime import datetime
from kiwoom import *

s_year_date = '2019-01-01';
s_standard_date = '2019-01-03'
e_standard_date = '2019-01-04'

class JkAtm:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def run(self):
        self.run_condition_auto_trade()

    def run_condition_auto_trade(self):
        #조건검색 로드
        self.kiwoom.get_condition_load()
        #조건검색 주식가져오기
        self.kiwoom.send_condition("0150", "스캘퍼_시가갭", "011", 1)
        code_list = self.kiwoom.condition_code_list[:-1]
        print(code_list)
        # 주식선정
        # 1) 정치 테마주, 자연재해관련주(씽크홀, 에볼라 같은 자연재해주)는 제외)
        # 2) 재료 소멸성 뉴스가 나왔을 경우 반드시 2번째 갭을 띄운 날짜에 기관의 순매수가 있어야 진입 가능

        # 금일날짜
        today = datetime.today().strftime("%Y%m%d")
        #df_krx = fdr.StockListing('KRX')
        #print(df_krx.head())
        #대상종목의 매수가 산정을 위한 가격데이타 수집
        df = fdr.DataReader(code_list[1],s_year_date)
        print(df['Close'][s_standard_date]) # 5%이상상승당일 종가
        print(df['Open'][e_standard_date])  # 매수전날 시가
        print(df['Close'][e_standard_date]) # 매수전날 종가

        #매수가능 구간 가격 조회
        s_buy_close_price_t = df['Close'][s_standard_date]
        e_buy_open_price_t  = df['Open'][e_standard_date]
        e_buy_close_price_t = df['Close'][e_standard_date]
        if(e_buy_open_price_t > e_buy_close_price_t):
            self.e_buy_price = e_buy_close_price_t
        else:
            self.e_buy_price = e_buy_open_price_t

        if(s_buy_close_price_t > self.e_buy_price):
            self.s_buy_price = self.e_buy_price
            self.e_buy_price = s_buy_close_price_t
        else:
            self.s_buy_price = s_buy_close_price_t
            self.e_buy_price = self.e_buy_price

        print(self.s_buy_price)
        print(self.e_buy_price)
        # 1) 매매대상 코드, 매매주가 범위(start_price,end_price)
        # 2) 뉴스키워드 검색
        # result = []
        # for i, code in enumerate(code_list):
        #     print("%d : %d" % (i, len(code_list)))
        #     if i > 100:
        #         break
        #
        #     (per, pbr) = self.get_per_pbr(code)
        #     if 2.5 <= per <= 10:
        #         result.append((code, per, pbr))
        #
        # data = sorted(result, key=lambda x:x[2])
        # self.dump_data(data[:30])

app = QApplication(sys.argv)
jkAtm = JkAtm()
jkAtm.run()