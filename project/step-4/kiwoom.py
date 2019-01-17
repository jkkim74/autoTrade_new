# -*-coding: utf-8 -
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import jk_util, util
import sys, os, re, datetime, copy, json
from datetime import datetime

# 추가 매수 진행시 stoploss 및 stopplus 퍼센티지 변경 최대 6
STOP_PLUS_PER_MAESU_COUNT = [ 8,                    8,                      8,                      8,                      8                  ]
STOP_LOSS_PER_MAESU_COUNT = [ 40,                   40,                     40,                     40,                     40,                ]
SLIPPAGE = 0.3 # 보통가로 거래하므로 매매 수수료만 적용
CHEGYEOL_INFO_FILE_PATH = "log" + os.path.sep +  "chegyeol.json"
JANGO_INFO_FILE_PATH =  "log" + os.path.sep + "jango.json"

class Kiwoom(QAxWidget):
    #sigBuy = pyqtSignal()
    order_result = -1
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self.order_loop = None
        self._set_signal_slot()
        self.jangoInfo = {}  # { 'jongmokCode': { '이익실현가': 222, ...}}
        self.michegyeolInfo = {}
        self.chegyeolInfo = {}  # { '날짜' : [ [ '주문구분', '매도', '주문/체결시간', '체결가' , '체결수량', '미체결수량'] ] }
        self.currentTime = datetime.now()

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
        self.order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga_type, order_no])

        if order_type != 2:
            self.order_loop = QEventLoop()
            self.order_loop.exec_()

    def get_login_info(self, tag):
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print('gubun :', gubun)
        # print(util.whoami() + 'gubun: {}, itemCnt: {}, fidList: {}'
        #         .format(gubun, itemCnt, fidList))
        if (gubun == "1"):  # 잔고 정보
            print('##################### : ', gubun)
            # 잔고 정보에서는 매도/매수 구분이 되지 않음

            jongmok_code = self.get_chejan_data(jk_util.name_fid['종목코드'])[1:]
            self.boyou_suryang = int(self.get_chejan_data(jk_util.name_fid['보유수량']))
            self.jumun_ganeung_suryang = int(self.get_chejan_data(jk_util.name_fid['주문가능수량']))
            self.maeip_danga = int(self.get_chejan_data(jk_util.name_fid['매입단가']))
            jongmok_name = self.get_chejan_data(jk_util.name_fid['종목명']).strip()
            current_price = abs(int(self.get_chejan_data(jk_util.name_fid['현재가'])))
            print('종목코드 : ', jongmok_code)
            print('보유수량 : ', self.boyou_suryang)
            print('주문가능수량 : ', self.jumun_ganeung_suryang)
            print('매입단가 : ', self.maeip_danga)
            print('종목명 : ', jongmok_name)
            print('현재가 : ', current_price)
            # 미체결 수량이 있는 경우 잔고 정보 저장하지 않도록 함
            if (jongmok_code in self.michegyeolInfo):
                if (self.michegyeolInfo[jongmok_code]['미체결수량']):
                    return
                    # 미체결 수량이 없으므로 정보 삭제
            del (self.michegyeolInfo[jongmok_code])
            if (self.boyou_suryang == 0):
                # 보유 수량이 0 인 경우 매도 수행
                if (jongmok_code not in self.todayTradedCodeList):
                    self.todayTradedCodeList.append(jongmok_code)
                self.jangoInfo.pop(jongmok_code)
                self.removeConditionOccurList(jongmok_code)
            #else:
                # 보유 수량이 늘었다는 것은 매수수행했다는 소리임
            #   self.sigBuy.emit()

                # 아래 잔고 정보의 경우 TR:계좌평가잔고내역요청 필드와 일치하게 만들어야 함
                current_jango = {}
                current_jango['보유수량'] = self.boyou_suryang
                current_jango['매매가능수량'] = self.jumun_ganeung_suryang  # TR 잔고에서 매매가능 수량 이란 이름으로 사용되므로
                current_jango['매입가'] = self.maeip_danga
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
            print('##################### : ', gubun)
            jumun_sangtae = self.get_chejan_data(jk_util.name_fid['주문상태'])
            self.jongmok_code = self.get_chejan_data(jk_util.name_fid['종목코드'])[1:]
            michegyeol_suryang = int(self.get_chejan_data(jk_util.name_fid['미체결수량']))
            maedo_maesu_gubun = self.get_chejan_data(jk_util.name_fid['매도매수구분'])
            if maedo_maesu_gubun == "1":
                print('주문상태 : ', '매도', jumun_sangtae)
            else:
                print('주문상태 : ', '매수', jumun_sangtae)
            print('종목코드 : ', self.jongmok_code)
            print('미체결수량 : ', michegyeol_suryang)
            # 주문 상태
            # 매수 시 접수(gubun-0) - 체결(gubun-0) - 잔고(gubun-1)
            # 매도 시 접수(gubun-0) - 잔고(gubun-1) - 체결(gubun-0) - 잔고(gubun-1)   순임
            # 미체결 수량 정보를 입력하여 잔고 정보 처리시 미체결 수량 있는 경우에 대한 처리를 하도록 함
            if (self.jongmok_code not in self.michegyeolInfo):
                self.michegyeolInfo[self.jongmok_code] = {}
            self.michegyeolInfo[self.jongmok_code]['미체결수량'] = michegyeol_suryang

            if (jumun_sangtae == "체결"):
                self.makeChegyeolInfo(self.jongmok_code, fid_list)
                self.makeChegyeolInfoFile()
                pass

            pass

        if(len(self.michegyeolInfo) == 0):
            try:
                self.order_loop.exit()
            except:
                pass
        else:
            print('미체결수량 : ', self.michegyeolInfo[self.jongmok_code]['미체결수량'])
            if(self.michegyeolInfo[self.jongmok_code]['미체결수량'] == 0):
                try:
                    self.order_loop.exit()
                except:
                    pass

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

    def makeChegyeolInfo(self, jongmok_code, fidList):
        fids = fidList.split(";")
        printData = ""
        info = []

        # 미체결 수량이 0 이 아닌 경우 다시 체결 정보가 올라 오므로 0인경우 처리 안함 
        michegyeol_suryung = int(self.get_chejan_data(jk_util.name_fid['미체결수량']).strip())
        if (michegyeol_suryung != 0):
            return
        nFid = jk_util.name_fid['매도매수구분']
        result = self.get_chejan_data(nFid).strip()
        maedo_maesu_gubun = '매도' if result == '1' else '매수'
        # 첫 매수시는 잔고 정보가 없을 수 있으므로 
        current_jango = self.jangoInfo.get(jongmok_code, {})

        #################################################################################################
        # 사용자 정의 컬럼 수익과 수익율 필드 채움 
        if (maedo_maesu_gubun == '매도'):
            # 체결가를 통해 수익율 필드 업데이트 
            current_price = int(self.get_chejan_data(jk_util.name_fid['체결가']).strip())
            self.calculateSuik(jongmok_code, current_price)

            # 매도시 체결정보는 수익율 필드가 존재 
            profit = current_jango.get('수익', '0')
            profit_percent = current_jango.get('수익율', '0')
            chumae_count = int(current_jango.get('매수횟수', '0'))
            maedo_type = current_jango.get('매도중', '')
            if (maedo_type == ''):
                maedo_type = '수동매도'
            info.append('{0:>10}'.format(profit_percent))
            info.append('{0:>10}'.format(profit))
            info.append(' 매수횟수: {0:>1} '.format(chumae_count))
            info.append(' {0} '.format(maedo_type))
            pass
        elif (maedo_maesu_gubun == '매수'):
            # 매수시 체결정보는 수익율 / 수익 필드가  
            info.append('{0:>10}'.format('0'))
            info.append('{0:>10}'.format('0'))
            # 체결시는 매수 횟수 정보가 업데이트 되지 않았기 때문에 +1 해줌  
            chumae_count = int(current_jango.get('매수횟수', '0'))
            info.append(' 매수횟수: {0:>1} '.format(chumae_count + 1))
            info.append(' {0} '.format('(단순매수)'))

        #################################################################################################
        # kiwoom api 체결 정보 필드 
        for col_name in jk_util.dict_jusik["체결정보"]:
            nFid = None
            result = ""
            if (col_name not in jk_util.name_fid):
                continue

            nFid = jk_util.name_fid[col_name]

            if (str(nFid) in fids):
                result = self.get_chejan_data(nFid).strip()
                if (col_name == '종목코드'):
                    result = result[1:]
                if (col_name == '체결가'):
                    result = '{0:>10}'.format(result)

                if (col_name == '체결량' or col_name == '미체결수량'):
                    result = '{0:>7}'.format(result)

                info.append(' {} '.format(result))
                printData += col_name + ": " + result + ", "

        current_date = self.currentTime.date().strftime('%y%m%d')

        if (current_date not in self.chegyeolInfo):
            self.chegyeolInfo[current_date] = []

            #################################################################################################
        # 매도시 매수 이력 정보 필드 
        if (maedo_maesu_gubun == '매도'):
            info.append(' ' + '\\t'.join(current_jango['체결가/체결시간']))
            pass

        self.chegyeolInfo[current_date].append('|'.join(info))
        util.save_log(printData, "*체결정보", folder="log")
        pass

    @pyqtSlot()
    def makeJangoInfoFile(self):
        print(util.whoami())
        remove_keys = [ '매도호가1','매도호가2', '매도호가수량1', '매도호가수량2', '매도호가총잔량',
                        '매수호가1', '매수호가2', '매수호가수량1', '매수호가수량2', '매수호가수량3', '매수호가수량4', '매수호가총잔량',
                        '현재가', '호가시간', '세금', '전일종가', '현재가', '종목번호', '수익율', '수익', '잔고' , '매도중', '시가', '고가', '저가', '장구분',
                        '거래량', '등락율', '전일대비', '기준가', '상한가', '하한가', '5분봉타임컷기준' ]
        temp = copy.deepcopy(self.jangoInfo)
        # 불필요 필드 제거
        for jongmok_code, contents in temp.items():
            for key in remove_keys:
                if( key in contents):
                    del contents[key]

        with open(JANGO_INFO_FILE_PATH, 'w', encoding = 'utf8' ) as f:
            f.write(json.dumps(temp, ensure_ascii= False, indent= 2, sort_keys = True ))
        pass

    def calculateSuik(self, jongmok_code, current_price):
        current_jango = self.jangoInfo[jongmok_code]
        maeip_price = abs(int(current_jango['매입가']))
        boyou_suryang = int(current_jango['보유수량'])

        suik_price = round( (current_price - maeip_price) * boyou_suryang , 2)
        current_jango['수익'] = suik_price
        current_jango['수익율'] = round( ( (current_price-maeip_price)  / maeip_price ) * 100 , 2)
        pass