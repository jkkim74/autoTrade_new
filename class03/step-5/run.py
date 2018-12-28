import sys
from PyQt5.QtWidgets import *
from kiwoom import *


app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.comm_connect()

account_list = kiwoom.get_login_info("ACCNO")
account = account_list.split(';')[0]

kiwoom.send_order("send_order", "0101", account, 1, "000660", 10, 0, "03", "")
