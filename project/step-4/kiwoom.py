from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import jk_util, util
import os
import json

# 추가 매수 진행시 stoploss 및 stopplus 퍼센티지 변경 최대 6
STOP_PLUS_PER_MAESU_COUNT = [ 8,                    8,                      8,                      8,                      8                  ]
STOP_LOSS_PER_MAESU_COUNT = [ 40,                   40,                     40,                     40,                     40,                ]
SLIPPAGE = 0.3 # 보통가로 거래하므로 매매 수수료만 적용
CHEGYEOL_INFO_FILE_PATH = "log" + os.path.sep +  "chegyeol.json"

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self.order_loop = None
        self._set_signal_slot()
        self.jangoInfo = {}  # { 'jongmokCode': { '이익실현가': 222, ...}}

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slot(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveConditionVer.connect(self._receive_condition_ver)
        self.OnReceiveTrCondition.connect(self._receive_tr_condition)

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
            self.high = self.get_comm_data(trcode, rqname, 0, "상한가")
            self.cur_price = self.get_comm_data(trcode, rqname, 0, "현재가")
        elif rqname == "opt10086_req":
            self.e_price = self.get_comm_data(trcode, rqname, 0, "종가")
            self.s_price = self.get_comm_data(trcode, rqname, 0, "시가")
        try:
            self.tr_loop.exit()
        except:
            pass

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga_type, order_no):
        result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga_type, order_no])
        if (result == 0):
            print("매수주문을 하였습니다.")
        self.order_loop = QEventLoop()
        self.order_loop.exec_()

    def get_login_info(self, tag):
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("get_chejan_data(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print('gubun :',gubun)
        print(fid_list)
        # print(util.whoami() + 'gubun: {}, itemCnt: {}, fidList: {}'
        #         .format(gubun, itemCnt, fidList))
        if (gubun == "1"):  # 잔고 정보
            # 잔고 정보에서는 매도/매수 구분이 되지 않음

            jongmok_code = self.get_chejan_data(jk_util.name_fid['종목코드'])[1:]
            boyou_suryang = int(self.get_chejan_data(jk_util.name_fid['보유수량']))
            jumun_ganeung_suryang = int(self.get_chejan_data(jk_util.name_fid['주문가능수량']))
            maeip_danga = int(self.get_chejan_data(jk_util.name_fid['매입단가']))
            jongmok_name = self.get_chejan_data(jk_util.name_fid['종목명']).strip()
            current_price = abs(int(self.get_chejan_data(jk_util.name_fid['현재가'])))

            # 미체결 수량이 있는 경우 잔고 정보 저장하지 않도록 함
            if (jongmok_code in self.michegyeolInfo):
                if (self.michegyeolInfo[jongmok_code]['미체결수량']):
                    return
                    # 미체결 수량이 없으므로 정보 삭제
            del (self.michegyeolInfo[jongmok_code])
            if (boyou_suryang == 0):
                # 보유 수량이 0 인 경우 매도 수행
                if (jongmok_code not in self.todayTradedCodeList):
                    self.todayTradedCodeList.append(jongmok_code)
                self.jangoInfo.pop(jongmok_code)
                self.removeConditionOccurList(jongmok_code)
            else:
                # 보유 수량이 늘었다는 것은 매수수행했다는 소리임
                self.sigBuy.emit()

                # 아래 잔고 정보의 경우 TR:계좌평가잔고내역요청 필드와 일치하게 만들어야 함
                current_jango = {}
                current_jango['보유수량'] = boyou_suryang
                current_jango['매매가능수량'] = jumun_ganeung_suryang  # TR 잔고에서 매매가능 수량 이란 이름으로 사용되므로
                current_jango['매입가'] = maeip_danga
                current_jango['종목번호'] = jongmok_code
                current_jango['종목명'] = jongmok_name.strip()
                chegyeol_info = util.cur_date_time('%Y%m%d%H%M%S') + ":" + str(current_price)

                if (jongmok_code not in self.jangoInfo):
                    current_jango['주문/체결시간'] = [util.cur_date_time('%Y%m%d%H%M%S')]
                    current_jango['체결가/체결시간'] = [chegyeol_info]
                    current_jango['최근매수가'] = [current_price]
                    current_jango['매수횟수'] = 1

                    self.jangoInfo[jongmok_code] = current_jango

                else:
                    chegyeol_time_list = self.jangoInfo[jongmok_code]['주문/체결시간']
                    chegyeol_time_list.append(util.cur_date_time('%Y%m%d%H%M%S'))
                    current_jango['주문/체결시간'] = chegyeol_time_list

                    last_chegyeol_info = self.jangoInfo[jongmok_code]['체결가/체결시간'][-1]
                    if (int(last_chegyeol_info.split(':')[1]) != current_price):
                        chegyeol_info_list = self.jangoInfo[jongmok_code]['체결가/체결시간']
                        chegyeol_info_list.append(chegyeol_info)
                        current_jango['체결가/체결시간'] = chegyeol_info_list

                    price_list = self.jangoInfo[jongmok_code]['최근매수가']
                    last_price = price_list[-1]
                    if (last_price != current_price):
                        # 매수가 나눠져서 진행 중이므로 자료 매수횟수 업데이트 안함
                        price_list.append(current_price)
                    current_jango['최근매수가'] = price_list

                    chumae_count = self.jangoInfo[jongmok_code]['매수횟수']
                    if (last_price != current_price):
                        current_jango['매수횟수'] = chumae_count + 1
                    else:
                        current_jango['매수횟수'] = chumae_count

                    self.jangoInfo[jongmok_code].update(current_jango)

            self.makeEtcJangoInfo(jongmok_code)
            self.makeJangoInfoFile()
            pass

        elif (gubun == "0"):
            jumun_sangtae = self.get_chejan_data(jk_util.name_fid['주문상태'])
            jongmok_code = self.get_chejan_data(jk_util.name_fid['종목코드'])[1:]
            michegyeol_suryang = int(self.get_chejan_data(jk_util.name_fid['미체결수량']))
            # 주문 상태
            # 매수 시 접수(gubun-0) - 체결(gubun-0) - 잔고(gubun-1)
            # 매도 시 접수(gubun-0) - 잔고(gubun-1) - 체결(gubun-0) - 잔고(gubun-1)   순임
            # 미체결 수량 정보를 입력하여 잔고 정보 처리시 미체결 수량 있는 경우에 대한 처리를 하도록 함
            if (jongmok_code not in self.michegyeolInfo):
                self.michegyeolInfo[jongmok_code] = {}
            self.michegyeolInfo[jongmok_code]['미체결수량'] = michegyeol_suryang

            if (jumun_sangtae == "체결"):
                self.makeChegyeolInfo(jongmok_code, fid_list)
                self.makeChegyeolInfoFile()
                pass

            pass
        # fid_info = []
        # fid_info = fid_list.split(';')
        # for fid in fid_info:
        #      print(fid , self.get_chejan_data(fid))
        #print(self.get_chejan_data(9203))
        # print(self.get_chejan_data(302))
        # print(self.get_chejan_data(900))
        # print(self.get_chejan_data(901))
        # try:
        #     self.order_loop.exit()
        # except:
        #     pass

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self.get_comm_data(trcode, rqname, i, "일자")
            open = self.get_comm_data(trcode, rqname, i, "시가")
            high = self.get_comm_data(trcode, rqname, i, "고가")
            low = self.get_comm_data(trcode, rqname, i, "저가")
            close = self.get_comm_data(trcode, rqname, i, "현재가")
            volume = self.get_comm_data(trcode, rqname, i, "거래량")

            print(date, open, high, low, close, volume)

    def get_condition_load(self):
        self.dynamicCall("GetConditionLoad()")
        self.condition_load_loop = QEventLoop()
        self.condition_load_loop.exec_()

    def _receive_condition_ver(self, ret, msg):
        if ret == 1:
            print("조건식 저장 성공")
        else:
            print("조건식 저장 실패")

        self.condition_load_loop.exit()

    def get_condition_name_list(self):
        ret =  self.dynamicCall("GetConditionNameList()")
        print(ret)

    def send_condition(self, screen_no, condition_name, index, search):
        self.dynamicCall("SendCondition(QString, QString, int, int)",
                         screen_no, condition_name, index, search)
        self.condition_tr_loop = QEventLoop()
        self.condition_tr_loop.exec_()

    def _receive_tr_condition(self, screen_no, code_list, condition_name, index, next ):
        print(condition_name)
        self.condition_code_list = code_list.split(";")
        #print(code_list)
        self.condition_tr_loop.exit()
        #return code_list


    # 첫 잔고 정보 요청시 호출됨
    # 매수, 매도후 체결 정보로 잔고 정보 올때 호출됨
    def makeEtcJangoInfo(self, jongmok_code, priority='server'):

        if (jongmok_code not in self.jangoInfo):
            return
        current_jango = {}

        if (priority == 'server'):
            current_jango = self.jangoInfo[jongmok_code]
            maeip_price = current_jango['매입가']

            if ('매수횟수' not in current_jango):
                if (jongmok_code in self.jangoInfoFromFile):
                    current_jango['매수횟수'] = self.jangoInfoFromFile[jongmok_code].get('매수횟수', 1)
                else:
                    current_jango['매수횟수'] = 1
                    pass

            maesu_count = current_jango['매수횟수']
            # 손절가 다시 계산
            stop_loss_value = STOP_LOSS_PER_MAESU_COUNT[maesu_count - 1]
            stop_plus_value = STOP_PLUS_PER_MAESU_COUNT[maesu_count - 1]

            current_jango['손절가'] = round(maeip_price * (1 - (stop_loss_value - SLIPPAGE) / 100), 2)
            current_jango['이익실현가'] = round(maeip_price * (1 + (stop_plus_value + SLIPPAGE) / 100), 2)

            if ('주문/체결시간' not in current_jango):
                if (jongmok_code in self.jangoInfoFromFile):
                    current_jango['주문/체결시간'] = self.jangoInfoFromFile[jongmok_code].get('주문/체결시간', [])
                else:
                    current_jango['주문/체결시간'] = []

            if ('체결가/체결시간' not in current_jango):
                if (jongmok_code in self.jangoInfoFromFile):
                    current_jango['체결가/체결시간'] = self.jangoInfoFromFile[jongmok_code].get('체결가/체결시간', [])
                else:
                    current_jango['체결가/체결시간'] = []

            if ('최근매수가' not in current_jango):
                if (jongmok_code in self.jangoInfoFromFile):
                    current_jango['최근매수가'] = self.jangoInfoFromFile[jongmok_code].get('최근매수가', [])
                else:
                    current_jango['최근매수가'] = []
        else:

            if (jongmok_code in self.jangoInfoFromFile):
                current_jango = self.jangoInfoFromFile[jongmok_code]
            else:
                current_jango = self.jangoInfo[jongmok_code]

        self.jangoInfo[jongmok_code].update(current_jango)
        pass


    def makeChegyeolInfoFile(self):
        # print(util.whoami())
        with open(CHEGYEOL_INFO_FILE_PATH, 'w', encoding = 'utf8' ) as f:
            f.write(json.dumps(self.chegyeolInfo, ensure_ascii= False, indent= 2, sort_keys = True ))
        pass
