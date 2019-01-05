import sys
from PyQt5.QtWidgets import *
import FinanceDataReader as fdr
from datetime import datetime
from kiwoom import *

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
        # 금일날짜
        today = datetime.today().strftime("%Y%m%d")
        #df_krx = fdr.StockListing('KRX')
        #print(df_krx.head())
        #대상종목의 매수가 산정을 위한 가격데이타 수집
        df = fdr.DataReader(code_list[1],'2019-01-03','2019-01-04')
        print(df['Close']['2019-01-03']) # 5%이상상승당일 종가
        print(df['Open']['2019-01-04'])  # 매수전날 시가
        print(df['Close']['2019-01-04']) # 매수전날 종가

        #매수가능 구간 가격 조회
        #self.s_buy_price =

app = QApplication(sys.argv)
jkAtm = JkAtm()
jkAtm.run()