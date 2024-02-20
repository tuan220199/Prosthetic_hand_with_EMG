from PyQt5 import QtCore

class Communicate(QtCore.QObject):
    data_signal = QtCore.pyqtSignal(list)