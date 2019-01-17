import threading
from time import sleep, ctime
from kiwoom import *

loops = [8,2]

class MyThread(threading.Thread):
    def __init__(self,func,args,name=''):
        threading.Thread.__init__(self,name=name)
        self.func = func
        self.args = args
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

    def run (self):
        self.func(*self.args)
        # 함수를 받아서 처리하는게 아니라 여기에 직접 구현하는 경우가 일반적..

def loop(nloop,nsec):
    print('start loop', nloop, 'at:',ctime())
    sleep(nsec)
    print('loop', nloop, 'at:', ctime())


def test() :
    print('starting at:', ctime())
    threads = []
    nloops = range(len(loops))

    for i in nloops:
        t = MyThread(loop, (i,loops[i]),loop.__name__)
        threads.append(t)

    for i in nloops:
        threads[i].start()

    for i in nloops:
        threads[i].join()

    print('all Done at: ', ctime())

if  __name__ == '__main__' :
   test()