import threading

class StockAuto(threading.Thread):
    def print_epoch(self,nameOfThread):
        for _ in range(10):
            print(nameOfThread,'-------------',threading.currentThread().getName())


x = threading.Thread(target=StockAuto.print_epoch,args=(StockAuto,'Thread1'))#StockAuto(name="메세지를 보냈습니다.")
y = threading.Thread(target=StockAuto.print_epoch,args=(StockAuto,'Thread2'))#StockAuto(name="메세지를 받았습니다.")
x.start()
y.start()
x.join()
y.join()
