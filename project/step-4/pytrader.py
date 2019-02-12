import sys
from PyQt5.QtWidgets import *
from kiwoom import *
from datetime import datetime
import FinanceDataReader as fdr
import time
import pickle
import util, jk_util
import threading

TEST_MODE = True
s_year_date = '2019-01-01';
#s_standard_date = '2019-01-04'
#e_standard_date = '2019-01-07'
global_buy_stock_code_list = ['016380', '021040']
if TEST_MODE:
    total_buy_money = 10000
else:
    total_buy_money = 1000#30000000
maesu_start_time = 90100
maesu_end_time  = 153000
maemae_logic = 'S'  # 'S':시가갭매매 'R':램덤매매
order_method = "00" # "00":보통매매, "03":시장가매매
class PyTrader(QMainWindow):
    def __init__(self):
        self.kiwoom = Kiwoom()
        if self.kiwoom.get_connect_state() == 0:
            self.kiwoom.comm_connect()
        self.order_type = 1      #1:매수,2:매도
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 300, 300, 150)

        btn1 = QPushButton("Login", self)
        btn1.move(20, 20)
        btn1.clicked.connect(self.btn1_clicked)

        btn2 = QPushButton("Check state", self)
        btn2.move(20, 70)
        btn2.clicked.connect(self.btn2_clicked)
        self.maesu_jongmok = []

    def btn1_clicked(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")

    def btn2_clicked(self):
        if self.kiwoom.dynamicCall("GetConnectState()") == 0:
            self.statusBar().showMessage("Not connected")
        else:
            self.statusBar().showMessage("Connected")

    def get_account(self):
        account_list = self.kiwoom.get_login_info("ACCNO")
        print(account_list)
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

    def run(self):
        if(maemae_logic == 'S'):
            self.S_mae_mae()
        elif(maemae_logic == 'R'):
            self.R_mae_mae()
        #매수
        #for code in codes:
        #    self.kiwoom.send_order("send_order", "0101", account, 1, code, 10, 0, "03", "")
        #    print(code)
    def R_mae_mae(self):
        account = self.get_account()
        nQty = 1
        stock_price = '6720'
        # 조건검색을 통해 저장한 데이타 가져오기
        local_buy_stock_code_list = self.load_data()
        # buy_stock_code = local_buy_stock_code_list[0]
        # buy_stock_code = global_buy_stock_code_list[0]
        for buy_stock_code in local_buy_stock_code_list:
            self.kiwoom.send_order("send_order", "0101", account, 1, buy_stock_code, nQty, stock_price, "03", "") #매수:1, 매도:2
            result = self.kiwoom.order_result
            if (result == 0):
                print("매수주문을 하였습니다.")
            else:
                print("매수 실패하였습니다.")

    def S_mae_mae(self):
        account = self.get_account()
        print("계좌정보 : ",account)
        # 금일날짜
        today   = datetime.today().strftime("%Y%m%d")
        today_f = datetime.today().strftime("%Y%m%d")
        prev_bus_day = util.get_prev_date(1,2,today)
        if prev_bus_day == None:
            print('매수일이 아닙니다.')
            prev_bus_day = util.get_prev_date(1, 2, str(int(today) - 1))
            if prev_bus_day == None:
                prev_bus_day = util.get_prev_date(1, 2, str(int(today) - 2))
        # 조건검색을 통해 저장한 데이타 가져오기
        if(len(global_buy_stock_code_list) > 0):
            local_buy_stock_code_list = global_buy_stock_code_list
        else:
            if len(sys.argv) > 1:
                local_buy_stock_code_list = [sys.argv[1]]#self.load_data()
            else:
                local_buy_stock_code_list = self.load_data()

        print('조건검색 코드 :',local_buy_stock_code_list)
        # codes = [x[0] for x in data]
        # print(data)
        # print(codes)
        # end
        s_standard_date = prev_bus_day[1]
        e_standard_date = prev_bus_day[0]
        print('5%이상상승당일 : ', s_standard_date, '시가갭날짜 : ', e_standard_date)
        while True:
            for buy_stock_code in local_buy_stock_code_list:
                if buy_stock_code in self.maesu_jongmok:
                    continue
                # 주식 bus 날짜 정보
                self._stock_bus_info(buy_stock_code, s_standard_date, e_standard_date)
                # 금일 시가 조회
                self.d_open_price = self.get_start_price(buy_stock_code, today_f)
                if self.d_open_price[0] == '-' or self.d_open_price[0] == '+':
                    self.d_open_price = self.d_open_price[1:]
                self.d_open_price = int(self.d_open_price)
                # self.e_buy_price = 4050
                print("시작가:", self.s_buy_price, ", 종료가:", self.e_buy_price, ", 당일시작가:", self.d_open_price)
                # 금일 시작가가 매수구간의 시작가보다 작으면 매수금지
                if self.s_buy_price > self.d_open_price:
                    # raise Exception("Can't Buy Stock")
                    print("### 매수당일 시가가 작업 주식매수 할수 없습니다.")
                    continue

                self._stock_maemae(account, buy_stock_code)


    def _stock_maemae(self, account, buy_stock_code):
        result = -1
        # ############### 주식주문 스타트 #################
        now_time = int(datetime.now().strftime('%H%M%S'))
        print('매매시간 : ', maesu_start_time, '~', maesu_end_time,' 현재시간 : ', now_time)
        if (maesu_end_time >= now_time >= maesu_start_time):
            cur_price = self.get_cur_price(buy_stock_code)
            if (cur_price[0] == '-' or cur_price[0] == '+'):
                cur_price = cur_price[1:]
            self.d_cur_price = int(cur_price)
            print('현재시간 : ', now_time, '현재가 : ', self.d_cur_price)
            #if ((self.e_buy_price >= self.d_cur_price >= self.s_buy_price) and (result == -1)):
            high_price = int(self.get_high(buy_stock_code))
            nQty = int(total_buy_money / self.d_cur_price)
            print(high_price, nQty)
            # TEST
            # high_price = 5690
            ##### TEST ####
            nQty = 1
            order_method = "03"
            ##### TEST ####
            self.kiwoom.send_order("send_order", "0101", account, self.order_type, buy_stock_code, nQty,
                                   high_price, order_method, "")
            result = self.kiwoom.order_result
            print('매수주문결과 : ', result)
            if (result == 0 or result == 1):
                if (self.order_type == 1):
                    print("매수주문을 하였습니다.")
                    self.maesu_jongmok.append(buy_stock_code)
            else:
                print("매수 실패하였습니다.")
        time.sleep(4)
        ############################### 주식 주문 종료 #########################################
        ############################### 확정 매도 주문 #########################################
        #if (result == 0 or result == 1):  # 매수주문 성공시에 확정매도 처리
        #    self._stock_mado_proc(account, buy_stock_code)

    def _stock_bus_info(self,buy_stock_code,s_standard_date,e_standard_date):
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

    def _stock_mado_proc(self, account, code):
        print('매도 :', account, code)
        maeip_danga = self.kiwoom.maeip_danga
        jumun_ganeung_suryang = self.kiwoom.jumun_ganeung_suryang
        maedo_price = self._get_maedo_price(maeip_danga)
        print(maeip_danga, jumun_ganeung_suryang, maedo_price)
        self.kiwoom.send_order("send_order", "0101", account, 2, code, jumun_ganeung_suryang, maedo_price, '00', "")#2:매도
        print("매도요청을 하였습니다.")


    def _get_maedo_price(self, price):
        s_price = int(price * 1.02)
        if (1000 <= s_price < 5000):
            r_price = round(s_price, -1) + 5
        elif (5000 <= s_price < 10000):
            dif = s_price % 5
            r_price = s_price - dif
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


    def load_data(self):
        try:
            f = open("./database.db", "rb")
            data = pickle.load(f)
            f.close()
            return data
        except:
            pass

    def processStopLoss(self,code):
        pass

app = QApplication(sys.argv)
pymon = PyTrader()
pymon.show()
pymon.run()
app.exec_()