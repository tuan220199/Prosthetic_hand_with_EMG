from PyQt5 import QtCore, QtWidgets

class PageWindow(QtWidgets.QMainWindow):
    
    gotoSignal = QtCore.pyqtSignal(str)
    
    def goto(self, name):
        self.gotoSignal.emit(name)

    def make_handleButton(self, button, *args):
        def handleButton():
            if button == "searchButton":
                self.goto("search")

            elif button == "scan":
                self.l1.setText("Scanning...")
                QtWidgets.qApp.processEvents()
                scan_results = self.GF.scan(5)
                if scan_results:
                    self.l1.setText(f"Found {len(scan_results)}")
                    for result in scan_results:
                        devButton = QtWidgets.QPushButton(f"{result}")
                        devButton.clicked.connect(self.make_handleButton("connectToDevice", result[2]))
                        self.layout.addWidget(devButton)
                else:
                    self.l1.setText("No bracelet was found")
                self.scanButton.setText("Scan Again")       
            elif button == "connectToDevice":
                try:
                    self.GF.connect(addr=args[0])
                    self.goto("menu")
                except:
                    pass

                                                        
        return handleButton
