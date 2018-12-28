import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock")
        self.setGeometry(300, 300, 300, 400)
        self.setWindowIcon(QIcon("icon.png"))

        btn = QPushButton("클릭", self)
        btn.move(20, 20)
        btn.clicked.connect(self.btn_clicked)

    def btn_clicked(self):
        QMessageBox.about(self, "클릭", "클릭됐습니다.")

app = QApplication(sys.argv)
mywindow = MyWindow()
mywindow.show()
app.exec_()
