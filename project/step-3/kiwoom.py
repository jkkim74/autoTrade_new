from PyQt5.QAxContainer import *
from PyQt5.QtCore import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slot()

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slot(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_loop = QEventLoop()
        self.login_loop.exec_()

    def _event_connect(self, err):
        if err == 0:
            print("로그인 성공")
        else:
            print("로그인 실패")

        self.login_loop.exit()

    def get_code_list_by_market(self, market):
        ret = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = ret.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        ret = self.dynamicCall("GetMasterCodeName(QString)", code)
        return ret

    def get_master_listed_stock_date(self, code):
        ret = self.dynamicCall("GetMasterListedStockDate(QString)", code)
        return ret

    def get_master_construction(self, code):
        ret = self.dynamicCall("GetMasterConstruction(QString)", code)
        return ret

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)",
                         rqname, trcode, next, screen_no);
        self.tr_loop = QEventLoop()
        self.tr_loop.exec_()

    def get_comm_data(self, trcode, rqname, index, item_name):
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               trcode, rqname, index, item_name)
        return ret.strip()

    def _receive_tr_data(self, screen_no, rqname, trcode, recode_name, next, unused1, unused2, unused3, unused4):
        if rqname == "opt10001_req":
            self.pbr = self.get_comm_data(trcode, rqname, 0, "PBR")
            self.per = self.get_comm_data(trcode, rqname, 0, "PER")
        try:
            self.tr_loop.exit()
        except:
            pass

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga_type, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga_type, order_no])
        # self.order_loop = QEventLoop()
        # self.order_loop.exec_()

    def get_login_info(self, tag):
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(self.get_chejan_data(900))
        try:
            self.order_loop.exit()
        except:
            pass



