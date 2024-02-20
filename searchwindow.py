from PyQt5 import  QtWidgets, QtCore, QtGui
from gforce import  DataNotifFlags
import os
from  pagewindow import PageWindow
from customcanvas import CustomFigCanvas
import threading
from datetime import datetime
from helpers import set_cmd_cb, rms_formuula
import random
from communicate import Communicate
import time
import numpy as np

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y%H:%M:%S")
os.makedirs(os.path.dirname(f"recordingfiles/{dt_string}.txt"), exist_ok=True)
file1 = open(f"recordingfiles/{dt_string}.txt","w")

sampRate = 500
channelMask = 0xFF
dataLen = 128
resolution = 8
channels = []
actions = list(range(1,10))*5
random.shuffle(actions)

OFFSET = 121
PEAK = 0
PEAK_MULTIPLIER = 0
ACTION = 0
REP = 0
BASELINE = 100
BASELINE_MULTIPLIER = 100
OFFSET_RMS = 0
STARTED = False
reg = None
packet_cnt = 0
start_time = 0
FORWARD = 0
ind_channel = 0

ACTIONS = {
    1: ["Flexion",          "img/Flexion.png",          (None, None),  0],
    2: ["Extension",        "img/Extension.png",        (None, None),  0],
    3: ["Ulnar Deviation",  "img/UlnarDeviation.png",   (None, None),  0],
    4: ["Radial Deviation", "img/RadialDeviation.png",  (None, None),  0],
    5: ["Supination",       "img/Supination.png",       (None, None),  0],
    6: ["Pronation",        "img/Pronation.png",        (None, None),  0],
    7: ["Open palm",        "img/Open.png",             (None, None),  0],
    8: ["Close palm",       "img/Close.png",            (None, None),  0],
    9: ["Rest",             "img/Rest.png",             (None, None),  0],
    }

class SearchWindow(PageWindow):
    """
    A class representing a window for scanning and connecting to devices.
    provides a user interface for scanning and connecting devices.
    inherits from the PageWindow class and extends its functionality.

    Attributes:
        GF (GForceProfile): An instance of the GForceProfile class for scanning and connecting to devices.
        devices  (): 

    
    Methods:
        initUI(): Initializes the user interface components and sets up the window.
        goToMain(): Navigates to the main page of the application.
        loadNewAction(newAction): Loads information and images related to a specific action.
        scan(): Initiates the device scanning process and updates the UI with scan results.
        connect(*args): Connects to a device using the provided arguments.
        make_handleButton(button, *args): Generates a button handler function based on the provided button type and arguments.
        addData_callbackFunc(value): Callback function for adding data to the UI.
        UiComponents(): Sets up the user interface components, including buttons and labels.
    """
    def __init__(self, GF):
        """
        Initializes a new instance of the SearchWindow class.

        Args:
            GF (GForceProfile): An instance of the GForceProfile class for scanning
                and connecting to devices.
        """
        super().__init__()
        self.initUI()
        self.GF = GF
        self.devices = []

    def initUI(self):
        """
        Initializes the user interface components and sets up the window.
        """
        self.setWindowTitle("Scan for device")
        self.setGeometry(100, 100, 1500, 900)
        self.UiComponents()

    def goToMain(self):
        """
        Navigates to the main page of the application.
        """
        self.goto("main")

    def loadNewAction(self, newAction):
        """
        Loads information and images related to a specific action. Set them into framework.

        Args:
            newAction (string): name of action to acess data in dictioanry ACTIONS.

        """
        global OFFSET_RMS, ACTIONS
        try:
            action_name, action_path, (action_baseline, action_peak), action_rep = ACTIONS[newAction]
            self.subj_motion.setText(f"{newAction}")
            self.subj_rep.setText(f"{action_rep}")
            self.actionLabel.setText(action_name)

            pixmap = QtGui.QPixmap(action_path)
            if not pixmap.isNull():
                self.actionImg.setPixmap(pixmap.scaledToWidth(150))
         
            if action_baseline:
                self.e2.setText(f"{action_peak-action_baseline}")
                self.myFig.update_amp(float(self.e3.text())* (action_peak-action_baseline))
                OFFSET_RMS = action_baseline
        except Exception as e:
            print("Error during loading Action: ", e)
    
    def scan(self):
        """
        Initiates the device scanning process and 
        updates the UI with scan results: set Text device found, create connect to device button.
        Create a button for device connect, layout2 add this button
        layout0 add layout2
        """
        scan_results = self.GF.scan(2)

        if scan_results:
            self.l1.setText(f"Found {len(scan_results)}")
            for result in scan_results:
                devButton = QtWidgets.QPushButton(f"{result[2]}")
                devButton.clicked.connect(self.make_handleButton("connectToDevice", result[2]))
                self.layout2.addWidget(devButton)
            self.layout0.addLayout(self.layout2)   
            self.layout2.setAlignment(QtCore.Qt.AlignTop)

        else:
            self.l1.setText("No bracelet was found")

    def connect(self,*args):
        """
        Connects to a device using the provided arguments.

        Args:
            *args: Additional arguments that may be required for connecting to the device.
        """
        try:
            self.GF.connect(addr=args[0])
        except:
            self.l1.setText(f"Can not conect to address {args[0]}. Please scan again.")
        while self.layout2.count():
            child = self.layout2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        QtWidgets.qApp.processEvents()

        self.l1.setText(f"Connected to {args[0]}")
        
    def make_handleButton(self, button, *args):
        """
        Generates a button handler function based on the provided button type and arguments.

        Creates a handler function for various button types in the user interface.
        The handler function performs different actions based on the button type and any additional arguments provided.

        Args:
            button (str): The type of button for which the handler function is being created.
            *args: Additional arguments that may be required for handling certain button types.

        Returns:
            function: A handler function for the specified button type.
            scan button: scan devices.
            connectToDevice: connect devices, set up configuration and data transfer for GF force device, update the fraemwork. 
            calibrate: calibrates the EMG data visualization scale and baseline.
            recordMVC: initiates recording of Maximum Voluntary Contraction (MVC) data.
            pauseMVC: Pause record MVC data and save data.
            startRecord: Initiates the recording process for experimental data.
            loadMotion: Loads a new motion/action for recording.
            stopRecord: Stop adn save the raw EMG data into file.
            updateMotion: LOad new action.
        """
        def handleButton():
            global reg,  ACTION, REP, PEAK, PEAK_MULTIPLIER, OFFSET, STARTED, BASELINE, BASELINE_MULTIPLIER
            global OFFSET_RMS, file1
            
            if button == "scan":
                """
                Set text scan to the button.
                run method scan 
                """
                self.l1.setText("Scanning...")
                QtWidgets.qApp.processEvents()
                self.scan()
                self.scanButton.setText("Scan Again")       
            
            elif button == "connectToDevice":
                """
                Connect the device 
                Set up configuration and data transfer for GF force device
                set window titlte, layout2 adds layout flo and layout4, layout0 adds layout subj_flo, layout5
                Load first action is first action in dictionary.
                layout adds layout3
                Create myFig (instance of CustomFigCanvas) and adds to layout. 
                Create and execute myDataLoop thread
                """
                self.connect(*args)
                QtWidgets.qApp.processEvents()

                self.GF.setEmgRawDataConfig(sampRate, channelMask, dataLen, resolution, cb=set_cmd_cb, timeout=1000)
                self.GF.setDataNotifSwitch(DataNotifFlags['DNF_EMG_RAW'], set_cmd_cb, 1000)
                self.GF.startDataNotification(ondata)

                self.setWindowTitle("Visualize EMG Data")

                self.layout2.addLayout(self.flo)
                self.layout2.addLayout(self.layout4) 

                self.layout0.addLayout(self.subj_flo)
                self.layout0.addLayout(self.layout5)

                self.loadNewAction(1)
                self.layout.addLayout(self.layout3)
                
                QtWidgets.qApp.processEvents()

                while True:
                    if len(channels)>128: 
                        break
                self.myFig = CustomFigCanvas()
                self.layout.addWidget(self.myFig)
                #Add the callbackfunc to ..
                myDataLoop = threading.Thread(name = 'myDataLoop', target = dataSendLoop, daemon = True, args = (self.addData_callbackFunc,))
                myDataLoop.start()

            elif button == "caliberate":
                """
                Update the figure based text vaöue of e1, e3, e2 and BASELINES
                """
                self.myFig.update_scale(int(self.e1.text()))
                self.myFig.update_amp(float(self.e3.text())* (float(self.e2.text())-BASELINE))
                OFFSET_RMS = BASELINE

            elif button == "recordMVC":
                """
                Set the PEAK_MULTIPLIER, BASELINE_MULTIPLIER, and OFFSET_RMS, to prepare for recording
                """
                PEAK_MULTIPLIER = 1
                BASELINE_MULTIPLIER = 1
                OFFSET_RMS = 0
                BASELINE = 10
                self.recordMVCButton.setText("Recording...")
                self.pauseMVCButton.setEnabled(True)
                self.recordMVCButton.setEnabled(False)

            elif button == "pauseMVC":
                """
                Define the current action by the value text of subj_motion.
                Update the the current action in the dictionary with BASELINE, PEAK, 
                Load the next action.
                """
                current_action = int(self.subj_motion.text())
                ACTIONS[current_action][2] = (BASELINE, PEAK)
                ACTIONS[current_action][3] = 1

                #self.e2.setText(f"{PEAK * PEAK_MULTIPLIER}")
                PEAK_MULTIPLIER = 0
                PEAK = 0
                BASELINE_MULTIPLIER = 100

                self.recordMVCButton.setText("Record MVC")
                self.pauseMVCButton.setEnabled(False)
                self.recordMVCButton.setEnabled(True)
                self.loadNewAction( current_action+ 1)

            elif button == "startRecord":
                """
                Update the amplitude of figure by e3*e2
                open the file in folder recordingfiles 
                """
                self.myFig.update_amp(float(self.e3.text())* float(self.e2.text()))
                self.recordSamplButton.setText("Recording ...")
                self.recordSamplButton.setEnabled(False)
                self.loadMotionButton.setEnabled(False)
                file1 = open(f"recordingfiles/{dt_string}.txt","w")
                STARTED= True

            elif button == "loadMotion":
                """
                Because action is a list of random actions: actions * repetitions 
                load the first element of list actions
                Update the number of actiosn left.
                """
                self.loadNewAction(actions.pop(0))
                self.loadMotionButton.setText(f"Load Random Motion ({len(actions)} left)")
            
            elif button == "stopRecord":
                """
                Open the folder, open the file text based on subject, shift, motion, rep
                Update the current action last element value +1 
                Set adn enable the Record Experiment. 
                """
                STARTED = False
                file1.close()
                os.makedirs(os.path.dirname(f"Subject_{self.subj_name.text()}/Shift_{self.subj_shift.text()}/"), exist_ok=True)
                name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
                                                             f"Subject_{self.subj_name.text()}/Shift_{self.subj_shift.text()}/Motion_{self.subj_motion.text()}_Rep_{self.subj_rep.text()}.txt",  
                                                             "Text Files(*.txt)")
                
                try:
                    print(name)
                    os.makedirs(os.path.dirname(name[0]), exist_ok=True)
                    os.system(f'cp {file1.name} {name[0]}')  
                    current_action = int(self.subj_motion.text())
                    ACTIONS[current_action][-1] += 1
                    self.loadMotionButton.setEnabled(True)
                except Exception as e:
                    print("Error during saving: ", e)

                self.recordSamplButton.setText("Record Experiment")
                self.recordSamplButton.setEnabled(True)
                

            elif button == "updateMotion":
                """
                Load new action.
                """
                try:
                    self.loadNewAction(int(self.subj_motion.text()))
                except Exception as e:
                    print("Error during update motion: ", e)

            elif button=='trainModel':
                self.trainModelButton.setText('Back to Collection Mode')
                self.trainModelButton.clicked.connect(self.make_handleButton("backToCollect"))
                QtWidgets.qApp.processEvents()
                reg = load_NonLinearmodel()

            elif button=='backToCollect':
                
                self.trainModelButton.clicked.connect(self.make_handleButton("trainModel"))
                self.trainModelButton.setText('Train Model')
                QtWidgets.qApp.processEvents()
                reg = None
            elif button == "skipSignal":
                FORWARD += 1000

        return handleButton
    
    def addData_callbackFunc(self, value):
        """
        add new value to the myFig through method addData.
        """
        self.myFig.addData(value)

    def UiComponents(self):
        """
        Set up user interface components: buttons, labels, fields, layout of window.
        Main Layout(self.layout): 
            Child layout: layout0, layout3, self.myFig
            Contents: layout1("scan" button and label)

        layout0: 
            Child layout: layout1, layout2, layout4, layout5, Subject Form Layout
            Contents: layout1("scan" button and label)

        layout1:
            child widget: "scan" button and label

        layout2: 
            Child layout: layout flo, layout4

        layout3:
            Child Widgets: Input fields and buttons related to calibration and recording

        layout4:
            Child Widgets: Buttons related to recording MVC and calibration (self.recordMVCButton, self.pauseMVCButton, caliberateButton)
        
        layout5:
            Child Widgets: Label and image related to the current action being performed (self.actionLabel, self.actionImg)
        
        Form Layout (self.flo):
            Contents: Input fields for EMG scale, peak, and MVC scale (self.e1, self.e2, self.e3)
        
        Subject Form Layout (self.subj_flo):
            Contents: Input fields for subject name, motion, repetition, and shift (self.subj_name, self.subj_motion, self.subj_rep, self.subj_shift)
        """
        global actions
        self.layout = QtWidgets.QVBoxLayout()
        self.layout0 = QtWidgets.QHBoxLayout()

        self.layout1 = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(10,10,10,10)
        self.layout.setSpacing(10)
        self.scanButton = QtWidgets.QPushButton("Scan")
        self.scanButton.setFixedSize(100,30)
        self.scanButton.clicked.connect(self.make_handleButton("scan"))
        self.l1 = QtWidgets.QLabel()
        self.l1.setText("Click Scan to start scanning")
        self.l1.setFixedSize(300,30)
        
        self.layout1.addWidget(self.scanButton)
        self.layout1.addWidget(self.l1)
        self.layout1.setAlignment(QtCore.Qt.AlignTop)

        self.layout0.addLayout(self.layout1)
        self.layout0.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addLayout(self.layout0)

        
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)

        self.setCentralWidget(widget)

        self.layout2 = QtWidgets.QVBoxLayout()


        self.layout3 = QtWidgets.QHBoxLayout()
        self.e1 = QtWidgets.QLineEdit("20")
        self.e1.setValidator(QtGui.QIntValidator())
        self.e1.setMaxLength(4)
        self.e1.setAlignment(QtCore.Qt.AlignLeft)
        self.e1.setFixedSize(200, 32)


        self.e2 = QtWidgets.QLineEdit("0")
        self.e2.setValidator(QtGui.QDoubleValidator(0,1,2))
        self.e2.setAlignment(QtCore.Qt.AlignLeft)
        self.e2.setFixedSize(200, 32)

        self.e3 = QtWidgets.QLineEdit("0.3")
        self.e3.setValidator(QtGui.QDoubleValidator(0,1,2))
        self.e3.setAlignment(QtCore.Qt.AlignLeft)
        self.e3.setFixedSize(200, 32)

        self.flo = QtWidgets.QFormLayout()
        
        self.flo.addRow("EMG Scale          ",self.e1)
        self.flo.addRow("Peak               ",self.e2)
        self.flo.addRow("MVC Scale          ",self.e3)

        self.layout4 = QtWidgets.QHBoxLayout()
        
        self.layout4.setAlignment(QtCore.Qt.AlignLeft)
        caliberateButton = QtWidgets.QPushButton("Caliberate")
        caliberateButton.clicked.connect(self.make_handleButton("caliberate"))
        caliberateButton.setFixedSize(120,30)

        self.recordMVCButton = QtWidgets.QPushButton("Record MVC")
        self.recordMVCButton.clicked.connect(self.make_handleButton("recordMVC"))
        self.recordMVCButton.setFixedSize(100,30)

        self.pauseMVCButton = QtWidgets.QPushButton("Pause")
        self.pauseMVCButton.setEnabled(False)
        self.pauseMVCButton.clicked.connect(self.make_handleButton("pauseMVC"))
        self.pauseMVCButton.setFixedSize(100,30)

        self.layout4.addWidget(self.recordMVCButton)
        self.layout4.addWidget(self.pauseMVCButton)
        self.layout4.addWidget(caliberateButton)

        self.loadMotionButton = QtWidgets.QPushButton(f"Load Random Motion ({len(actions)} left)")
        self.loadMotionButton.clicked.connect(self.make_handleButton("loadMotion"))
        self.loadMotionButton.setFixedSize(300,30)

        self.recordSamplButton = QtWidgets.QPushButton("Record Experiment")
        self.recordSamplButton.clicked.connect(self.make_handleButton("startRecord"))
        self.recordSamplButton.setFixedSize(150,30)
        
        stopSamplButton = QtWidgets.QPushButton("Stop")
        stopSamplButton.clicked.connect(self.make_handleButton("stopRecord"))
        stopSamplButton.setFixedSize(150,30)

        self.trainModelButton = QtWidgets.QPushButton("Train model")
        self.trainModelButton.clicked.connect(self.make_handleButton("trainModel"))
        self.trainModelButton.setFixedSize(150,30)
        
        self.skipSignalButton = QtWidgets.QPushButton("Refresh")
        self.skipSignalButton.clicked.connect(self.make_handleButton("skipSignal"))
        self.skipSignalButton.setFixedSize(150,30)

        self.layout3.addWidget(self.loadMotionButton)
        self.layout3.addWidget(self.recordSamplButton)
        self.layout3.addWidget(stopSamplButton)
        self.layout3.addWidget(self.skipSignalButton)

        self.subj_name = QtWidgets.QLineEdit("1")
        self.subj_name.setValidator(QtGui.QIntValidator())
        self.subj_name.setMaxLength(4)
        self.subj_name.setAlignment(QtCore.Qt.AlignLeft)
        self.subj_name.setFixedSize(150, 32)

        self.subj_motion = QtWidgets.QLineEdit("1")
        self.subj_motion.setValidator(QtGui.QDoubleValidator(0,1,2))
        self.subj_motion.textEdited.connect(self.make_handleButton("updateMotion"))
        self.subj_motion.setAlignment(QtCore.Qt.AlignLeft)
        self.subj_motion.setFixedSize(150, 32)

        self.subj_rep = QtWidgets.QLineEdit("1")
        self.subj_rep.setValidator(QtGui.QIntValidator())
        self.subj_rep.setAlignment(QtCore.Qt.AlignLeft)
        self.subj_rep.setFixedSize(150, 32)

        self.subj_shift = QtWidgets.QLineEdit("0")
        self.subj_shift.setValidator(QtGui.QIntValidator())
        self.subj_shift.setAlignment(QtCore.Qt.AlignLeft)
        self.subj_shift.setFixedSize(150, 32)

        self.subj_flo = QtWidgets.QFormLayout()
        
        self.subj_flo.addRow("Subject       ",self.subj_name)
        self.subj_flo.addRow("Motion        ",self.subj_motion)
        self.subj_flo.addRow("Rep           ",self.subj_rep)
        self.subj_flo.addRow("Shift         ",self.subj_shift)

        self.layout5 = QtWidgets.QVBoxLayout()
        self.layout5.setAlignment(QtCore.Qt.AlignCenter)
        self.layout5.setContentsMargins(0, 0, 0, 0)

        self.actionLabel = QtWidgets.QLabel()
        self.actionLabel.setFont(QtGui.QFont('Arial', 20))
        self.actionLabel.setFixedSize(300,30)
        self.actionLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.actionImg = QtWidgets.QLabel()
        self.actionImg.setAlignment(QtCore.Qt.AlignCenter)
        self.layout5.addWidget(self.actionLabel)
        self.layout5.addWidget(self.actionImg)

def ondata(data):
    """
    Function to write data into a gloabl file: file1 

    Args:
    data (array 2 dimens/ Pandan dataframe): The raw data.
    
    """
    global STARTED, channels, file1

        # Data for EMG CH0~CHn repeatly.
        # Resolution set in setEmgRawDataConfig:
        #   8: one byte for one channel
        #   12: two bytes in LSB for one channel.
        # eg. 8bpp mode, data[1] = channel[0], data[2] = channel[1], ... data[8] = channel[7]
        #                data[9] = channel[0] and so on
        # eg. 12bpp mode, {data[2], data[1]} = channel[0], {data[4], data[3]} = channel[1] and so on

        # # end for
        
    extracted_data = data[1:]
    channels += extracted_data

    if STARTED:
        file1.write(' '.join(map(str, extracted_data)) +"\n")

def dataSendLoop(addData_callbackFunc):
    # Setup the signal-slot mechanism.
    """
    Continuous loop for sending data to the callback function for plotting.

    Args:
        addData_callbackFunc (function): Callback function to which the data is sent.

    This function sets up the signal-slot mechanism and continuously sends data to the specified callback function for plotting.
    It iterates over the data channels, calculates features, and emits the data to the callback function.

    Note:
        This function assumes the availability of global variables: PEAK, PEAK_MULTIPLIER, BASELINE, OFFSET_RMS, BASELINE_MULTIPLIER,
        ACTIONS, FORWARD, and reg.

    """
    mySrc = Communicate()
    mySrc.data_signal.connect(addData_callbackFunc)
    #time.sleep(3)
    global PEAK, PEAK_MULTIPLIER, BASELINE, OFFSET_RMS, BASELINE_MULTIPLIER,ACTIONS,FORWARD, reg
    while(True):
        #channels[i:i+50*8]
        for j in range (8):
            try:
                datawindow = channels[FORWARD:FORWARD+50*8]
                if datawindow:
                    datastack = np.stack([np.array(datawindow[k::8]) for k in range (8)]).astype('float32') - OFFSET
                    mean_in_window = datastack.mean(1) # should have size (8,)
                    rms_ = rms_formuula(datastack/255)
                    rms = rms_.sum()- OFFSET_RMS
                    
                    if OFFSET_RMS:
                        mySrc.data_signal.emit([rms] + list(mean_in_window))
                    else:
                        BASELINE = min(rms*BASELINE_MULTIPLIER, BASELINE)
                        PEAK = max(rms*PEAK_MULTIPLIER, PEAK)
                        mySrc.data_signal.emit([rms] + list(mean_in_window))
                    FORWARD += 25*8 
                time.sleep(47/1000)


            except Exception as e:
                print("Error during plotting:", type(e),e) 
