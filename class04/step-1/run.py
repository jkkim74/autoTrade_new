import sys
from PyQt5.QtWidgets import *
from kiwoom import *
import time

app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.comm_connect()

kiwoom.set_input_value("종목코드", "039490")
kiwoom.set_input_value("기준일자", "20171210")
kiwoom.set_input_value("수정주가구분", 1)
kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

while kiwoom.remained_data == True:
    time.sleep(3)
    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.set_input_value("기준일자", "20171210")
    kiwoom.set_input_value("수정주가구분", 1)
    kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")