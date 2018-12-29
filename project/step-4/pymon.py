import sys
from PyQt5.QtWidgets import *
from kiwoom import *
import time
import pickle

class PyMon:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def run(self):
        #self.run_pbr_per_screener()
        self.run_condition_data()

    def run_condition_data(self):
        self.kiwoom.get_condition_load()
        #self.kiwoom.get_condition_name_list()
        self.kiwoom.send_condition("0150", "스캘퍼_시가갭", "011", 1)
        #print(self.kiwoom.condition_code_list[:-1])
        code_list = self.kiwoom.condition_code_list[:-1]
        r_price = self.get_condition_param(code_list[0], "20181227")
        print(r_price)

    def run_pbr_per_screener(self):
        code_list = self.kiwoom.get_code_list_by_market(0) + self.kiwoom.get_code_list_by_market(10)

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
    def get_condition_param(self, code, s_date):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("시작일자", s_date)
        self.kiwoom.comm_rq_data("opt10086_req", "opt10086", 0, "0101")
        return (self.kiwoom.s_price, self.kiwoom.e_price)

    def get_per_pbr(self, code):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
        time.sleep(0.2)
        return (float(self.kiwoom.per), float(self.kiwoom.pbr))

    def dump_data(self, data):
        f = open("./database.db", "wb")
        pickle.dump(data, f)
        f.close()

app = QApplication(sys.argv)
pymon = PyMon()
pymon.run()
