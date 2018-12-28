import sys
from PyQt5.QtWidgets import *
from kiwoom import *
import pickle

class PyTrader:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def get_account(self):
        account_list = self.kiwoom.get_login_info("ACCNO")
        return account_list.split(';')[0]

    def run(self):
        account = self.get_account()
        data = self.load_data()
        codes = [x[0] for x in data]
        print(data)
        print(codes)

        for code in codes:
            self.kiwoom.send_order("send_order", "0101", account, 1, code, 10, 0, "03", "")
            print(code)

    def load_data(self):
        try:
            f = open("./database.db", "rb")
            data = pickle.load(f)
            f.close()
            return data
        except:
            pass

app = QApplication(sys.argv)
pymon = PyTrader()
pymon.run()