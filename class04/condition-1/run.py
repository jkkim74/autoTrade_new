import sys
from PyQt5.QtWidgets import *
from kiwoom import *

app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.comm_connect()

# 조건식 불러오기
kiwoom.get_condition_load()

