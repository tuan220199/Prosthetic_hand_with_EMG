from PyQt5 import QtCore, QtWidgets

class PageWindow(QtWidgets.QMainWindow):
    """
    A class to represent a start window and make_handleButton function.

    Attributes:
    
    Methods:
        goto: Navigates to other pages in application
        make_handleButton(button, *args): Generates a button handler function based on the provided button type and arguments.
    """
    gotoSignal = QtCore.pyqtSignal(str)
    
    def goto(self, name):
        self.gotoSignal.emit(name)

    def make_handleButton(self, button, *args):
        """
        creates a handler function for a button click event. The handler function
        performs different actions based on the type of button clicked.

        Args:
            self: Reference to the current instance of the class.
            button (str): The type of button for which the handler function is being created.
            *args: Additional arguments that may be required for handling certain types of buttons.

        Returns:
            function: A handler function for the specified button type.
        """
        def handleButton():
            """
            searchButton button click: Navigates to search page
            scan button click: scan devices 
            connectToDevice button click: Connect device and Navigates to menu page
            """
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
