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
        self.run_pbr_per_screener()

    def run_pbr_per_screener(self):
        code_list = self.kiwoom.get_code_list_by_market(0) + self.kiwoom.get_code_list_by_market(10)

        result = []
        for i, code in enumerate(code_list):
            print("%d : %d" % (i, len(code_list)))

            (per, pbr) = self.get_per_pbr(code)
            if 2.5 <= per <= 10:
                result.append((code, per, pbr))

        data = sorted(result, key=lambda x:x[2])
        self.dump_data(data)

    def get_per_pbr(self, code):
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
        time.sleep(1)
        return (float(self.kiwoom.per), float(self.kiwoom.pbr))

    def dump_data(self, data):
        f = open("./database.db", "wb")
        pickle.dump(data, f)
        f.close()

app = QApplication(sys.argv)
pymon = PyMon()
pymon.run()
