import sys
from PyQt5.QtWidgets import *
from kiwoom import *

app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.comm_connect()

# 조건식 불러오기
kiwoom.get_condition_load()
kiwoom.get_condition_name_list()
kiwoom.send_condition("0150", "스캘퍼_시가갭", "011", 1)