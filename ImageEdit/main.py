from PyQt5 import QtWidgets
from ui.window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()
