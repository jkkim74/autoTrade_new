import threading
import time

def sendOrder(code,name):
    while True:
        print("sendOrder ==>",code,name)
        time.sleep(1)


stock_list = ['126880', '006890']
threads = []
for stock in stock_list:
    name = threading.currentThread().getName()
    t = threading.Thread(target=sendOrder,args=(stock,name))
    threads.append(t)

for thread in threads:
    #thread.daemon = True
    thread.start()
    time.sleep(1)

for thread in threads:
    thread.join()
