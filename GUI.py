from PyQt5 import  QtWidgets
from gforce import GForceProfile
from  searchwindow import SearchWindow

if __name__ == "__main__":
    import sys

    GF = GForceProfile()
    app = QtWidgets.QApplication(sys.argv)
    w = SearchWindow(GF)
    w.show()
    sys.exit(app.exec_())