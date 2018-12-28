import sys
from PyQt5.QtWidgets import *
from kiwoom import *

class PyMon:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def run(self):
        print("run")

app = QApplication(sys.argv)
pymon = PyMon()
pymon.run()
