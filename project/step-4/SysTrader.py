#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
from collections import deque
import threading
from threading import Event
from threading import Lock
import logging
from logging import FileHandler

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import *
import FinanceDataReader as fdr
from datetime import datetime
import pickle
import numpy as np
import pandas as pd

import util

TEST_MODE = False
s_year_date = '2019-01-01';
if TEST_MODE:
    total_buy_money = 50000
else:
    total_buy_money = 10000000
maesu_start_time = 90000
maesu_end_time = 180000
global_buy_stock_code_list = ['016380', '021040']
ACCOUNT_NO = '8111294711'
# 상수
종목별매수상한 = 1000000  # 종목별매수상한 백만원
매수수수료비율 = 0.00015  # 매도시 평단가에 곱해서 사용
매도수수료비율 = 0.00015 + 0.003  # 매도시 현재가에 곱해서 사용
화면번호 = "1234"
if TEST_MODE:
    ACCNT_INDEX = 4
else:
    ACCNT_INDEX = 0

# 로그 파일 핸들러
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
fh_log = FileHandler(os.path.join(BASE_DIR, 'logs/debug.log'), encoding='utf-8')
fh_log.setLevel(logging.DEBUG)

# 로거 생성 및 핸들러 등록
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh_log)


class RequestThreadWorker(QObject):
    def __init__(self):
        """요청 쓰레드
        """
        super().__init__()
        self.request_queue = deque()  # 요청 큐
        self.request_thread_lock = Lock()

        # 간혹 요청에 대한 결과가 콜백으로 오지 않음
        # 마지막 요청을 저장해 뒀다가 일정 시간이 지나도 결과가 안오면 재요청
        self.retry_timer = None
        self.currentTime = datetime.now().__format__()

    def retry(self, request):
        logger.debug(util.cur_date_time() + " : 키움 함수 재시도: %s %s %s" % (request[0].__name__, request[1], request[2]))
        self.request_queue.appendleft(request)

    def run(self):
        while True:
            # 큐에 요청이 있으면 하나 뺌
            # 없으면 블락상태로 있음
            try:
                request = self.request_queue.popleft()
            except IndexError as e:
                time.sleep(2)
                continue

            # 요청 실행
            logger.debug(util.cur_date_time() + " : 키움 함수 실행: %s %s %s" % (request[0].__name__, request[1], request[2]))
            request[0](hts, *request[1], **request[2])

            # 요청에대한 결과 대기
            if not self.request_thread_lock.acquire(blocking=True, timeout=5):
                # 요청 실패
                time.sleep(2)
                self.retry(request)  # 실패한 요청 재시도

            time.sleep(2)  # 0.2초 이상 대기 후 마무리


class SyncRequestDecorator:
    """키움 API 비동기 함수 데코레이터
    """

    @staticmethod
    def kiwoom_sync_request(func):
        def func_wrapper(self, *args, **kwargs):
            if kwargs.get('nPrevNext', 0) == 0:
                logger.debug('초기 요청 준비')
                self.params = {}
                self.result = {}
            # self.request_thread_worker.request_queue.append((func, args, kwargs))
            logger.debug(util.cur_date_time() + " : 요청 실행: %s %s %s" % (func.__name__, args, kwargs))
            func(self, *args, **kwargs)
            self.event = QEventLoop()
            self.event.exec_()
            return self.result  # 콜백 결과 반환

        return func_wrapper

    @staticmethod
    def kiwoom_sync_callback(func):
        def func_wrapper(self, *args, **kwargs):
            logger.debug(util.cur_date_time() + " : 요청 콜백: %s %s %s" % (func.__name__, args, kwargs))
            func(self, *args, **kwargs)  # 콜백 함수 호출

        return func_wrapper


class Kiwoom(QAxWidget, QMainWindow):
    # 초당 5회 제한이므로 최소한 0.2초 대기해야 함
    # (2018년 10월 기준) 1시간에 1000회 제한하므로 3.6초 이상 대기해야 함
    연속요청대기초 = 4.0

    def __init__(self):
        """메인 객체
        """
        super().__init__()

        # 키움 시그널 연결
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self.kiwoom_OnEventConnect)
        self.OnReceiveTrData.connect(self.kiwoom_OnReceiveTrData)
        self.OnReceiveRealData.connect(self.kiwoom_OnReceiveRealData)
        self.OnReceiveConditionVer.connect(self.kiwoom_OnReceiveConditionVer)
        self.OnReceiveTrCondition.connect(self.kiwoom_OnReceiveTrCondition)
        self.OnReceiveRealCondition.connect(self.kiwoom_OnReceiveRealCondition)
        self.OnReceiveChejanData.connect(self.kiwoom_OnReceiveChejanData)
        self.OnReceiveMsg.connect(self.kiwoom_OnReceiveMsg)

        # 파라미터
        self.params = {}
        self.dict_stock = {}
        self.dict_callback = {}
        self.set_stock_ordered = []
        self.dict_holding = {}

        # 요청 결과
        self.event = None
        self.result = {}

        # window 창뛰우기
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 300, 300, 150)

        btn = QPushButton("Check state", self)
        btn.move(20, 70)
        btn.clicked.connect(self.btn_clicked)

        # 미체결정보
        self.michegyeolInfo = {}

    def run(self):
        print("== run ==")

    def btn_clicked(self):
        if self.kiwoom.dynamicCall("GetConnectState()") == 0:
            self.statusBar().showMessage("Not connected")
        else:
            self.statusBar().showMessage("Connected")

    # -------------------------------------
    # 로그인 관련함수
    # -------------------------------------
    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_CommConnect(self, **kwargs):
        """로그인 요청 (키움증권 로그인창 띄워줌. 자동로그인 설정시 바로 로그인 진행)
        OnEventConnect() 콜백
        :param kwargs:
        :return: 1: 로그인 요청 성공, 0: 로그인 요청 실패
        """
        lRet = self.dynamicCall("CommConnect()")
        return lRet

    def kiwoom_GetConnectState(self, **kwargs):
        """로그인 상태 확인
        OnEventConnect 콜백
        :param kwargs:
        :return: 0: 연결안됨, 1: 연결됨
        """
        lRet = self.dynamicCall("GetConnectState()")
        return lRet
    # ------------------------------------
    # 로그인 정보
    # ------------------------------------
    def _kiwoom_GetLoginInfo(self, tag):
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    def kiwoom_GetAccountNo(self):
        accountList = self._kiwoom_GetLoginInfo("ACCNO").split(";")
        return accountList[ACCNT_INDEX]

    @SyncRequestDecorator.kiwoom_sync_callback
    def kiwoom_OnEventConnect(self, nErrCode, **kwargs):
        """로그인 결과 수신
        로그인 성공시 [조건목록 요청]GetConditionLoad() 실행
        :param nErrCode: 0: 로그인 성공, 100: 사용자 정보교환 실패, 101: 서버접속 실패, 102: 버전처리 실패
        :param kwargs:
        :return:
        """
        if nErrCode == 0:
            logger.debug(util.cur_date_time() + " : 로그인 성공")
        elif nErrCode == 100:
            logger.debug(util.cur_date_time() + " : 사용자 정보교환 실패")
        elif nErrCode == 101:
            logger.debug(util.cur_date_time() + " : 서버접속 실패")
        elif nErrCode == 102:
            logger.debug(util.cur_date_time() + " : 버전처리 실패")

        self.result['result'] = nErrCode
        if self.event is not None:
            self.event.exit()

    # -------------------------------------
    # 조회 관련함수
    # -------------------------------------
    def kiwoom_SetInputValue(self, sID, sValue):
        """
        :param sID:
        :param sValue:
        :return:
        """
        res = self.dynamicCall("SetInputValue(QString, QString)", sID, sValue)
        return res

    def kiwoom_CommRqData(self, sRQName, sTrCode, nPrevNext, sScreenNo):
        """

        :param sRQName:
        :param sTrCode:
        :param nPrevNext:
        :param sScreenNo:
        :return:
        """
        res = self.dynamicCall("CommRqData(QString, QString, int, QString)", sRQName, sTrCode, nPrevNext, sScreenNo)
        return res

    def kiwoom_GetRepeatCnt(self, sTRCode, sRQName):
        """

        :param sTRCode:
        :param sRQName:
        :return:
        """
        res = self.dynamicCall("GetRepeatCnt(QString, QString)", sTRCode, sRQName)
        return res

    def kiwoom_GetCommData(self, sTRCode, sRQName, nIndex, sItemName):
        """

        :param sTRCode:
        :param sRQName:
        :param nIndex:
        :param sItemName:
        :return:
        """
        res = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTRCode, sRQName, nIndex, sItemName)
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPT10001_주식기본정보요청(self, strCode, **kwargs):
        """주식기본정보요청
        :param strCode:
        :param kwargs:
        :return:
        """
        res = self.kiwoom_SetInputValue("종목코드", strCode)
        res = self.kiwoom_CommRqData("주식기본정보", "OPT10001", 0, "0101")
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPT10080_주식분봉차트조회(self, strCode, tick=1, fix=1, size=240, nPrevNext=0, **kwargs):
        """주식분봉차트조회
        :param strCode: 종목코드
        :param tick: 틱범위 (1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분)
        :param fix: 수정주가구분 (0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
        :param nPrevNext:
        :param kwargs:
        :return:
        """
        self.params['size'] = size
        res = self.kiwoom_SetInputValue("종목코드", strCode)
        # res = self.kiwoom_SetInputValue("기준일자", 기준일자)
        res = self.kiwoom_SetInputValue("틱범위", str(tick))
        res = self.kiwoom_SetInputValue("수정주가구분", str(fix))
        res = self.kiwoom_CommRqData("주식분봉차트조회", "opt10080", nPrevNext, 화면번호)
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPT10081_주식일봉차트조회(self, strCode, tick=1, fix=1, size=240, nPrevNext=0, **kwargs):
        """주식일봉차트조회
        :param strCode: 종목코드
        :param tick: 틱범위
        :param fix: 수정주가구분 (0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
        :param nPrevNext:
        :param kwargs:
        :return:
        """
        self.params['size'] = size
        res = self.kiwoom_SetInputValue("종목코드", strCode)
        # res = self.kiwoom_SetInputValue("기준일자", 기준일자)
        res = self.kiwoom_SetInputValue("틱범위", str(tick))
        res = self.kiwoom_SetInputValue("수정주가구분", str(fix))
        res = self.kiwoom_CommRqData("주식일봉차트조회", "opt10081", nPrevNext, 화면번호)
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPT20006_업종일봉조회(self, strCode, size=240, nPrevNext=0, **kwargs):
        """업종일봉조회
        :param strCode: 업종코드 (001: 코스피, 002: 대형주, 003: 중형주, 004: 소형주, 101: 코스닥, 201: 코스피200, 302: KOSTAR, 701: KRX100)
        :param nPrevNext:
        :param kwargs:
        :return:
        """
        self.params['size'] = size
        res = self.kiwoom_SetInputValue("업종코드", strCode)
        # res = self.kiwoom_SetInputValue("기준일자", 기준일자)
        res = self.kiwoom_CommRqData("업종일봉조회", "opt20006", nPrevNext, 화면번호)
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPT10085_계좌수익률요청(self, 계좌번호, **kwargs):
        """계좌수익률요청
        :param 계좌번호: 계좌번호
        :param kwargs:
        :return:
        """
        res = self.kiwoom_SetInputValue("계좌번호", 계좌번호)
        res = self.kiwoom_CommRqData("계좌수익률요청", "opt10085", 0, 화면번호)
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_TR_OPW00001_예수금상세현황요청(self, 계좌번호, **kwargs):
        """계좌수익률요청
        :param 계좌번호: 계좌번호
        :param kwargs:
        :return:
        """
        res = self.kiwoom_SetInputValue("계좌번호", 계좌번호)
        res = self.kiwoom_CommRqData("예수금상세현황요청", "opw00001", 0, 화면번호)
        return res

    @SyncRequestDecorator.kiwoom_sync_callback
    def kiwoom_OnReceiveTrData(self, sScrNo, sRQName, sTRCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage,
                               sSPlmMsg, **kwargs):
        """TR 요청에 대한 결과 수신
        데이터 얻어오기 위해 내부에서 GetCommData() 호출
          GetCommData(
          BSTR strTrCode,   // TR 이름
          BSTR strRecordName,   // 레코드이름
          long nIndex,      // TR반복부
          BSTR strItemName) // TR에서 얻어오려는 출력항목이름
        :param sScrNo: 화면번호
        :param sRQName: 사용자 구분명
        :param sTRCode: TR이름
        :param sRecordName: 레코드 이름
        :param sPreNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
        :param nDataLength: 사용안함
        :param sErrorCode: 사용안함
        :param sMessage: 사용안함
        :param sSPlmMsg: 사용안함
        :param kwargs:
        :return:
        """

        if sRQName == "예수금상세현황요청":
            self.int_주문가능금액 = int(self.kiwoom_GetCommData(sTRCode, sRQName, 0, "주문가능금액"))
            logger.debug(util.cur_date_time() + " : 예수금상세현황요청: %s" % (self.int_주문가능금액,))
            if "예수금상세현황요청" in self.dict_callback:
                self.dict_callback["예수금상세현황요청"](self.int_주문가능금액)

        elif sRQName == "주식기본정보":
            cnt = self.kiwoom_GetRepeatCnt(sTRCode, sRQName)
            list_item_name = ["종목명", "현재가", "등락율", "거래량", "시가", "상한가"]
            종목코드 = self.kiwoom_GetCommData(sTRCode, sRQName, 0, "종목코드")
            종목코드 = 종목코드.strip()
            dict_stock = self.dict_stock.get(종목코드, {})
            for item_name in list_item_name:
                item_value = self.kiwoom_GetCommData(sTRCode, sRQName, 0, item_name)
                item_value = item_value.strip()
                dict_stock[item_name] = item_value
            self.dict_stock[종목코드] = dict_stock
            logger.debug(util.cur_date_time() + " : 주식기본정보: %s, %s" % (종목코드, dict_stock))
            if "주식기본정보" in self.dict_callback:
                self.dict_callback["주식기본정보"](dict_stock)

        elif sRQName == "시세표성정보":
            cnt = self.kiwoom_GetRepeatCnt(sTRCode, sRQName)
            list_item_name = ["종목명", "현재가", "등락률", "거래량"]
            dict_stock = {}
            for item_name in list_item_name:
                item_value = self.kiwoom_GetCommData(sTRCode, sRQName, 0, item_name)
                item_value = item_value.strip()
                dict_stock[item_name] = item_value
            if "시세표성정보" in self.dict_callback:
                self.dict_callback["시세표성정보"](dict_stock)

        elif sRQName == "주식분봉차트조회" or sRQName == "주식일봉차트조회":
            cnt = self.kiwoom_GetRepeatCnt(sTRCode, sRQName)

            종목코드 = self.kiwoom_GetCommData(sTRCode, sRQName, 0, "종목코드")
            종목코드 = 종목코드.strip()

            done = False  # 파라미터 처리 플래그
            result = self.result.get('result', [])
            cnt_acc = len(result)

            list_item_name = []
            if sRQName == '주식분봉차트조회':
                # list_item_name = ["현재가", "거래량", "체결시간", "시가", "고가",
                #                   "저가", "수정주가구분", "수정비율", "대업종구분", "소업종구분",
                #                   "종목정보", "수정주가이벤트", "전일종가"]
                list_item_name = ["체결시간", "시가", "고가", "저가", "현재가", "거래량"]
            elif sRQName == '주식일봉차트조회':
                list_item_name = ["일자", "시가", "고가", "저가", "현재가", "거래량"]

            for nIdx in range(cnt):
                item = {'종목코드': 종목코드}
                for item_name in list_item_name:
                    item_value = self.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name)
                    item_value = item_value.strip()
                    item[item_name] = item_value

                # 범위조회 파라미터
                date_from = int(self.params.get("date_from", "000000000000"))
                date_to = int(self.params.get("date_to", "999999999999"))

                # 결과는 최근 데이터에서 오래된 데이터 순서로 정렬되어 있음
                date = None
                if sRQName == '주식분봉차트조회':
                    date = int(item["체결시간"])
                elif sRQName == '주식일봉차트조회':
                    date = int(item["일자"])
                    if date > date_to:
                        continue
                    elif date < date_from:
                        done = True
                        break

                # 개수 파라미터처리
                if cnt_acc + nIdx >= self.params.get('size', float("inf")):
                    done = True
                    break

                result.append(util.convert_kv(item))

            # 차트 업데이트
            self.result['result'] = result

            if not done and cnt > 0 and sPreNext == '2':
                self.result['nPrevNext'] = 2
                self.result['done'] = False
            else:
                # 연속조회 완료
                logger.debug(util.cur_date_time() + " : 차트 연속조회완료")
                self.result['nPrevNext'] = 0
                self.result['done'] = True

        elif sRQName == "업종일봉조회":
            cnt = self.kiwoom_GetRepeatCnt(sTRCode, sRQName)

            업종코드 = self.kiwoom_GetCommData(sTRCode, sRQName, 0, "업종코드")
            업종코드 = 업종코드.strip()

            done = False  # 파라미터 처리 플래그
            result = self.result.get('result', [])
            cnt_acc = len(result)

            list_item_name = []
            if sRQName == '업종일봉조회':
                list_item_name = ["일자", "시가", "고가", "저가", "현재가", "거래량"]

            for nIdx in range(cnt):
                item = {'업종코드': 업종코드}
                for item_name in list_item_name:
                    item_value = self.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name)
                    item_value = item_value.strip()
                    item[item_name] = item_value

                # 결과는 최근 데이터에서 오래된 데이터 순서로 정렬되어 있음
                date = int(item["일자"])

                # 범위조회 파라미터 처리
                date_from = int(self.params.get("date_from", "000000000000"))
                date_to = int(self.params.get("date_to", "999999999999"))
                if date > date_to:
                    continue
                elif date < date_from:
                    done = True
                    break

                # 개수 파라미터처리
                if cnt_acc + nIdx >= self.params.get('size', float("inf")):
                    done = True
                    # break

                result.append(util.convert_kv(item))

            # 차트 업데이트
            self.result['result'] = result

            if not done and cnt > 0 and sPreNext == '2':
                self.result['nPrevNext'] = 2
                self.result['done'] = False
            else:
                # 연속조회 완료
                logger.debug(util.cur_date_time() + " : 차트 연속조회완료")
                self.result['nPrevNext'] = 0
                self.result['done'] = True

        elif sRQName == "계좌수익률요청":
            cnt = self.kiwoom_GetRepeatCnt(sTRCode, sRQName)
            for nIdx in range(cnt):
                list_item_name = ["종목코드", "종목명", "현재가", "매입가", "보유수량"]
                dict_holding = {item_name: self.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name).strip() for
                                item_name in list_item_name}
                dict_holding["현재가"] = util.safe_cast(dict_holding["현재가"], int, 0)
                # 매입가를 총매입가로 키변경
                dict_holding["총매입가"] = util.safe_cast(dict_holding["매입가"], int, 0)
                dict_holding["보유수량"] = util.safe_cast(dict_holding["보유수량"], int, 0)
                dict_holding["수익"] = (dict_holding["현재가"] - dict_holding["총매입가"]) * dict_holding["보유수량"]
                종목코드 = dict_holding["종목코드"]
                self.dict_holding[종목코드] = dict_holding
                logger.debug(util.cur_date_time() + " : 계좌수익: %s" % (dict_holding,))
            if '계좌수익률요청' in self.dict_callback:
                self.dict_callback['계좌수익률요청'](self.dict_holding)

        if self.event is not None:
            self.event.exit()

    # -------------------------------------
    # 실시간 관련함수
    # -------------------------------------
    def kiwoom_OnReceiveRealData(self, sCode, sRealType, sRealData, **kwargs):
        """
        실시간 데이터 수신
          OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 리얼타입
          BSTR sRealData    // 실시간 데이터 전문
          )
        :param sCode: 종목코드
        :param sRealType: 리얼타입
        :param sRealData: 실시간 데이터 전문
        :param kwargs:
        :return:
        """
        logger.debug(util.cur_date_time() + " : REAL: %s %s %s" % (sCode, sRealType, sRealData))

        if sRealType == "주식체결":
            pass

    def kiwoom_SetRealReg(self, strScreenNo, strCodeList, strFidList, strOptType):
        """
        SetRealReg(
          BSTR strScreenNo,   // 화면번호
          BSTR strCodeList,   // 종목코드 리스트
          BSTR strFidList,  // 실시간 FID리스트
          BSTR strOptType   // 실시간 등록 타입, 0또는 1 (0은 교체 등록, 1은 추가 등록)
          )
        :param str:
        :return:
        """
        lRet = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                                [strScreenNo, strCodeList, strFidList, strOptType])
        return lRet

    # -------------------------------------
    # 조건검색 관련함수
    # GetConditionLoad(), OnReceiveConditionVer(), SendCondition(), OnReceiveRealCondition()
    # -------------------------------------
    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_GetConditionLoad(self, **kwargs):
        """
        조건검색의 조건목록 요청
        :return:
        """
        lRet = self.dynamicCall("GetConditionLoad()")
        return lRet

    @SyncRequestDecorator.kiwoom_sync_callback
    def kiwoom_OnReceiveConditionVer(self, lRet, sMsg, **kwargs):
        """
        조건검색의 조건목록 결과 수신
        GetConditionNameList() 실행하여 조건목록 획득.
        첫번째 조건 이용하여 [조건검색]SendCondition() 실행
        :param lRet:
        :param sMsg:
        :param kwargs:
        :return:
        """
        if lRet:
            sRet = self.dynamicCall("GetConditionNameList()")
            pairs = [idx_name.split('^') for idx_name in [cond for cond in sRet.split(';')]]
            if len(pairs) > 0:
                nIndex = pairs[0][0]
                strConditionName = pairs[0][1]
                self.kiwoom_SendCondition(strConditionName, nIndex)

    def kiwoom_SendCondition(self, strConditionName, nIndex, **kwargs):
        """
        조검검색 실시간 요청. OnReceiveConditionVer() 안에서 호출해야 함.
        실시간 요청이라도 OnReceiveTrCondition() 콜백 먼저 호출됨.
        조검검색 결과 변경시 OnReceiveRealCondition() 콜백 호출됨.
          SendCondition(
          BSTR strScrNo,    // 화면번호
          BSTR strConditionName,  // 조건식 이름
          int nIndex,     // 조건명 인덱스
          int nSearch   // 조회구분, 0:조건검색, 1:실시간 조건검색
          )
        :param strConditionName: 조건식 이름
        :param nIndex: 조건명 인덱스
        :param kwargs:
        :return: 1: 성공, 0: 실패
        """
        lRet = self.dynamicCall(
            "SendCondition(QString, QString, int, int)",
            [화면번호, strConditionName, nIndex, 1]
        )
        return lRet

    @SyncRequestDecorator.kiwoom_sync_callback
    def kiwoom_OnReceiveTrCondition(self, sScrNo, strCodeList, strConditionName, nIndex, nNext, **kwargs):
        """
        조건검색 결과 수신
          OnReceiveTrCondition(
          BSTR sScrNo,    // 화면번호
          BSTR strCodeList,   // 종목코드 리스트
          BSTR strConditionName,    // 조건식 이름
          int nIndex,   // 조건명 인덱스
          int nNext   // 연속조회 여부
          )
        :param sScrNo: 화면번호
        :param strCodeList: 종목코드 리스트
        :param strConditionName: 조건식 이름
        :param nIndex: 조건명 인덱스
        :param nNext: 연속조회 여부
        :param kwargs:
        :return:
        """
        list_str_code = list(filter(None, strCodeList.split(';')))
        logger.debug(util.cur_date_time() + " : 조건검색 결과: %s" % (list_str_code,))

        # 조검검색 결과를 종목 모니터링 리스트에 추가
        self.set_stock2monitor.update(set(list_str_code))

    def kiwoom_OnReceiveRealCondition(self, strCode, strType, strConditionName, strConditionIndex, **kwargs):
        """
        실시간 조건검색 결과 수신
          OnReceiveRealCondition(
          BSTR strCode,   // 종목코드
          BSTR strType,   //  이벤트 종류, "I":종목편입, "D", 종목이탈
          BSTR strConditionName,    // 조건식 이름
          BSTR strConditionIndex    // 조건명 인덱스
          )
        :param strCode: 종목코드
        :param strType: 이벤트 종류, "I":종목편입, "D", 종목이탈
        :param strConditionName: 조건식 이름
        :param strConditionIndex: 조건명 인덱스
        :param kwargs:
        :return:
        """
        logger.debug(util.cur_date_time() + " : 실시간 조건검색: %s %s %s %s" % (strCode, strType, strConditionName, strConditionIndex))
        if strType == "I":
            # 모니터링 종목 리스트에 추가
            self.set_stock2monitor.add(strCode)
        elif strType == "D":
            # 모니터링 종목 리스트에서 삭제
            self.set_stock2monitor.remove(strCode)

    # -------------------------------------
    # 주문 관련함수
    # OnReceiveTRData(), OnReceiveMsg(), OnReceiveChejan()
    # -------------------------------------
    def kiwoom_SendOrder(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo,
                         **kwargs):
        """주문
        :param sRQName: 사용자 구분명
        :param sScreenNo: 화면번호
        :param sAccNo: 계좌번호 10자리
        :param nOrderType: 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
        :param sCode: 종목코드
        :param nQty: 주문수량
        :param nPrice: 주문가격
        :param sHogaGb: 거래구분(혹은 호가구분)은 아래 참고
          00 : 지정가
          03 : 시장가
          05 : 조건부지정가
          06 : 최유리지정가
          07 : 최우선지정가
          10 : 지정가IOC
          13 : 시장가IOC
          16 : 최유리IOC
          20 : 지정가FOK
          23 : 시장가FOK
          26 : 최유리FOK
          61 : 장전시간외종가
          62 : 시간외단일가매매
          81 : 장후시간외종가
        :param sOrgOrderNo: 원주문번호입니다. 신규주문에는 공백, 정정(취소)주문할 원주문번호를 입력합니다.
        :param kwargs:
        :return:
        """
        logger.debug(util.cur_date_time() + " : 주문: %s %s %s %s %s %s %s %s %s" % (
            sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo))
        lRet = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb,
                                 sOrgOrderNo])
        return lRet

    def kiwoom_OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg, **kwargs):
        """주문성공, 실패 메시지
        :param sScrNo: 화면번호
        :param sRQName: 사용자 구분명
        :param sTrCode: TR이름
        :param sMsg: 서버에서 전달하는 메시지
        :param kwargs:
        :return:
        """
        logger.debug(util.cur_date_time() + " : 주문/잔고: %s %s %s %s" % (sScrNo, sRQName, sTrCode, sMsg))

    def kiwoom_OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList, **kwargs):
        """주문접수, 체결, 잔고발생시
        :param sGubun: 체결구분 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4"
        :param nItemCnt:
        :param sFIdList:
        "9201" : "계좌번호"
        "9203" : "주문번호"
        "9001" : "종목코드"
        "913" : "주문상태"
        "302" : "종목명"
        "900" : "주문수량"
        "901" : "주문가격"
        "902" : "미체결수량"
        "903" : "체결누계금액"
        "904" : "원주문번호"
        "905" : "주문구분"
        "906" : "매매구분"
        "907" : "매도수구분"
        "908" : "주문/체결시간"
        "909" : "체결번호"
        "910" : "체결가"
        "911" : "체결량"
        "10" : "현재가"
        "27" : "(최우선)매도호가"
        "28" : "(최우선)매수호가"
        "914" : "단위체결가"
        "915" : "단위체결량"
        "919" : "거부사유"
        "920" : "화면번호"
        "917" : "신용구분"
        "916" : "대출일"
        "930" : "보유수량"
        "931" : "매입단가"
        "932" : "총매입가"
        "933" : "주문가능수량"
        "945" : "당일순매수수량"
        "946" : "매도/매수구분"
        "950" : "당일총매도손일"
        "951" : "예수금"
        "307" : "기준가"
        "8019" : "손익율"
        "957" : "신용금액"
        "958" : "신용이자"
        "918" : "만기일"
        "990" : "당일실현손익(유가)"
        "991" : "당일실현손익률(유가)"
        "992" : "당일실현손익(신용)"
        "993" : "당일실현손익률(신용)"
        "397" : "파생상품거래단위"
        "305" : "상한가"
        "306" : "하한가"
        :param kwargs:
        :return:
        """
        print("체결/잔고: %s %s %s" % (sGubun, nItemCnt, sFIdList))
        logger.debug(util.cur_date_time() + " : 체결/잔고: %s %s %s" % (sGubun, nItemCnt, sFIdList))
        if sGubun == '0':
            list_item_name = ["계좌번호", "주문번호", "관리자사번", "종목코드", "주문업무분류",
                              "주문상태", "종목명", "주문수량", "주문가격", "미체결수량",
                              "체결누계금액", "원주문번호", "주문구분", "매매구분", "매도수구분",
                              "주문체결시간", "체결번호", "체결가", "체결량", "현재가",
                              "매도호가", "매수호가", "단위체결가", "단위체결량", "당일매매수수료",
                              "당일매매세금", "거부사유", "화면번호", "터미널번호", "신용구분",
                              "대출일"]
            list_item_id = [9201, 9203, 9205, 9001, 912,
                            913, 302, 900, 901, 902,
                            903, 904, 905, 906, 907,
                            908, 909, 910, 911, 10,
                            27, 28, 914, 915, 938,
                            939, 919, 920, 921, 922,
                            923]
            dict_contract = {item_name: self.kiwoom_GetChejanData(item_id).strip() for item_name, item_id in
                             zip(list_item_name, list_item_id)}

            # 종목코드에서 'A' 제거
            종목코드 = dict_contract["종목코드"]
            if 'A' <= 종목코드[0] <= 'Z' or 'a' <= 종목코드[0] <= 'z':
                종목코드 = 종목코드[1:]
                dict_contract["종목코드"] = 종목코드

            # 종목을 대기 리스트에서 제거
            if 종목코드 in self.set_stock_ordered:
                self.set_stock_ordered.remove(종목코드)

            # 매수 체결일 경우 보유종목에 빈 dict 추가 (키만 추가하기 위해)
            if "매수" in dict_contract["주문구분"]:
                self.dict_holding[종목코드] = {}
            # 매도 체결일 경우 보유종목에서 제거
            else:
                self.dict_holding.pop(종목코드, None)

            logger.debug(util.cur_date_time() + " : 체결: %s" % (dict_contract,))
        if sGubun == '1':
            list_item_name = ["계좌번호", "종목코드", "신용구분", "대출일", "종목명",
                              "현재가", "보유수량", "매입단가", "총매입가", "주문가능수량",
                              "당일순매수량", "매도매수구분", "당일총매도손일", "예수금", "매도호가",
                              "매수호가", "기준가", "손익율", "신용금액", "신용이자",
                              "만기일", "당일실현손익", "당일실현손익률", "당일실현손익_신용", "당일실현손익률_신용",
                              "담보대출수량", "기타"]
            list_item_id = [9201, 9001, 917, 916, 302,
                            10, 930, 931, 932, 933,
                            945, 946, 950, 951, 27,
                            28, 307, 8019, 957, 958,
                            918, 990, 991, 992, 993,
                            959, 924]
            dict_holding = {item_name: self.kiwoom_GetChejanData(item_id).strip() for item_name, item_id in
                            zip(list_item_name, list_item_id)}
            dict_holding["현재가"] = util.safe_cast(dict_holding["현재가"], int, 0)
            dict_holding["보유수량"] = util.safe_cast(dict_holding["보유수량"], int, 0)
            dict_holding["매입단가"] = util.safe_cast(dict_holding["매입단가"], int, 0)
            dict_holding["총매입가"] = util.safe_cast(dict_holding["총매입가"], int, 0)
            dict_holding["주문가능수량"] = util.safe_cast(dict_holding["주문가능수량"], int, 0)

            # 종목코드에서 'A' 제거
            종목코드 = dict_holding["종목코드"]
            if 'A' <= 종목코드[0] <= 'Z' or 'a' <= 종목코드[0] <= 'z':
                종목코드 = 종목코드[1:]
                dict_holding["종목코드"] = 종목코드

                # 미체결 수량이 있는 경우 잔고 정보 저장하지 않도록 함
            if (종목코드 in self.michegyeolInfo):
                if (self.michegyeolInfo[종목코드]['미체결수량']):
                    return
                    # 미체결 수량이 없으므로 정보 삭제
            del (self.michegyeolInfo[종목코드])

            # 보유종목 리스트에 추가
            self.dict_holding[종목코드] = dict_holding

            logger.debug(util.cur_date_time() + " : 잔고: %s" % (dict_holding,))
            if self.dict_holding[종목코드]["보유수량"] > 0 and self.dict_holding[종목코드]["주문가능수량"] > 0:
                accountNo = hts.kiwoom_GetAccountNo()
                self._stock_mado_proc(accountNo, 종목코드)

    def kiwoom_GetChejanData(self, nFid):
        """
        OnReceiveChejan()이벤트 함수가 호출될때 체결정보나 잔고정보를 얻어오는 함수입니다.
        이 함수는 반드시 OnReceiveChejan()이벤트 함수가 호출될때 그 안에서 사용해야 합니다.
        :param nFid: 실시간 타입에 포함된FID
        :return:
        """
        res = self.dynamicCall("GetChejanData(int)", [nFid])
        return res

    def _stock_mado_proc(self, account, code):
        print('매도 :', account, code)
        maeip_danga = self.dict_holding[code]["매입단가"]
        jumun_ganeung_suryang = self.dict_holding[code]["주문가능수량"]
        maedo_price = self._get_maedo_price(maeip_danga)
        print(maeip_danga, jumun_ganeung_suryang, maedo_price)
        result = self.kiwoom_SendOrder("send_order", "0101", account, 2, code, jumun_ganeung_suryang, maedo_price, '00', "")#2:매도
        if (result == 0):
            print("매도처리를 하였습니다.")
        else:
            print("매도처리 실패하였습니다.")

    def _get_maedo_price(self, price):
        s_price = int(price * 1.02)
        if (1000 <= s_price < 5000):
            r_price = round(s_price, -1) + 5
        elif (5000 <= s_price < 10000):
            dif = s_price % 5
            r_price = s_price - dif
        elif (10000 <= s_price < 50000):
            r_price = round(s_price, -2)
        elif (50000 <= s_price < 100000):
            r_price = round(s_price, -2)
        elif (100000 <= s_price < 500000):
            dif = s_price % 500
            r_price = s_price - dif
        elif (s_price >= 500000):
            r_price = round(s_price, -3)
        else:
            r_price = s_price
        return r_price


def _isBuyStockAvailable(buy_stock_code, cur_price, start_price):
    bBuyStock = False

    if TEST_MODE:
        return True

    # 금일날짜
    today = datetime.today().strftime("%Y%m%d")
    today_f = datetime.today().strftime("%Y%m%d")
    prev_bus_day = util.get_prev_date(1, 2, today)
    if prev_bus_day == None:
        print('매수일이 아닙니다.')
        prev_bus_day = util.get_prev_date(1, 2, str(int(today) - 1))
        if prev_bus_day == None:
            prev_bus_day = util.get_prev_date(1, 2, str(int(today) - 2))
    s_standard_date = prev_bus_day[1]
    e_standard_date = prev_bus_day[0]
    # 대상종목의 매수가 산정을 위한 가격데이타 수집
    df = fdr.DataReader(buy_stock_code, s_year_date)
    print('### 5%이상상승당일 종가 : ', df['Close'][s_standard_date], '시가갭날 시가 : ', df['Open'][e_standard_date], '시가갭날 종가 : ',
          df['Close'][e_standard_date])  # 매수전날 시가

    # 매수가능 구간 가격 조회
    s_buy_close_price_t = df['Close'][s_standard_date]
    e_buy_open_price_t = df['Open'][e_standard_date]
    e_buy_close_price_t = df['Close'][e_standard_date]
    if (e_buy_open_price_t > e_buy_close_price_t):
        e_buy_price = int(e_buy_close_price_t)
    else:
        e_buy_price = int(e_buy_open_price_t)

    if (s_buy_close_price_t > e_buy_price):
        s_buy_price = int(e_buy_price)
        e_buy_price = int(s_buy_close_price_t)
    else:
        s_buy_price = int(s_buy_close_price_t)
        e_buy_price = int(e_buy_price)

    if start_price[0] == '-' or start_price[0] == '+':
        start_price = start_price[1:]

    if s_buy_price > int(start_price):
        print("금일 시가가 매수시작가보다 낮아 매수 불가합니다.")
        return False
    if cur_price[0] == '-' or cur_price[0] == '+':
        cur_price = cur_price[1:]
    if (e_buy_price >= int(cur_price) >= s_buy_price):
        bBuyStock = True
    else:
        bBuyStock = False
    print('### 매수범위 : ', s_buy_price, ' ~ ', e_buy_price, ' 현재가 : ', int(cur_price), ' 시가 : ', start_price, "매수가능여부 :",
          bBuyStock)  # 매수전날 시가
    return bBuyStock


def _isTimeAvalable():

    if TEST_MODE:
        return True
    now_time = int(datetime.now().strftime('%H%M%S'))
    if (maesu_end_time >= now_time >= maesu_start_time):
        return True
    else:
        print("매수가능한 시간이 아닙니다.", maesu_start_time, "~", maesu_end_time, " : ", now_time)
        return False


def load_data():
    try:
        f = open("./database.db", "rb")
        data = pickle.load(f)
        f.close()
        return data
    except:
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hts = Kiwoom()
    hts.show()
    result = -1
    order_type = 1
    # login
    if hts.kiwoom_GetConnectState() == 0:
        logger.debug('로그인 시도')
        res = hts.kiwoom_CommConnect()
        logger.debug('로그인 결과: {}'.format(res))
        accountNo = hts.kiwoom_GetAccountNo()# hts.kiwoom_GetLoginInfo()[4]
        print("계좌정보 :", accountNo)
        if len(global_buy_stock_code_list) > 0:
            local_buy_stock_code_list = global_buy_stock_code_list
        else:
            local_buy_stock_code_list = load_data()
        if len(local_buy_stock_code_list) > 0:
            while True:
                if _isTimeAvalable():
                    for code in local_buy_stock_code_list:
                        hts.kiwoom_TR_OPT10001_주식기본정보요청(code)
                        cur_price = hts.dict_stock[code].get('현재가')
                        start_price = hts.dict_stock[code].get('시가')
                        if _isBuyStockAvailable(code, cur_price, start_price):
                            high_price = int(hts.dict_stock[code].get('상한가'))
                            if cur_price[0] == '-' or cur_price[0] == '+':
                                buy_price = int(cur_price[1:])
                            else:
                                buy_price = int(cur_price)
                            nQty = int(total_buy_money / buy_price)
                            print("매수수량 : ", nQty, " 매수상한가 : ", high_price)
                            ### TEST ###
                            nQty = 1
                            result = hts.kiwoom_SendOrder("send_order", "0101", accountNo, order_type, code, nQty,
                                                          high_price, "03", "")
                            print(code, result)
                            if result == 0:
                                print("매수 요청 하였습니다.")
                                local_buy_stock_code_list.remove(code)
                            else:
                                print("매수 요청 실패하였습니다.")
                        else:
                            print("매수 불가합니다.")
                        hts.dict_stock[code] = {}
                time.sleep(3)
            else:
                print("매수 가능한 종목이 없습니다.")

        if res.get('result') != 0:
            sys.exit()

    # something
    app.exec_()
    pass

