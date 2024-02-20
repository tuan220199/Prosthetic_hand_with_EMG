import numpy as np
import queue
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.pyplot import subplots
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class CustomFigCanvas(FigureCanvas, TimedAnimation):
    def __init__(self):
        # The data
        self.scale = 20
        self.xlim = 200
        self.amplitude = 0.5
        self.addedData = queue.Queue()
        self.addedLabel = queue.Queue()
        self.timeline = np.arange(0,25,5)-25
        self.timelinex = np.arange(0,500,100)
        self.n = np.linspace(0, 299, 500)
        self.convolemask = np.ones(15)/15
        self.cue_line = np.zeros(500)
        self.extra = np.arange(0,self.scale*9,self.scale)
        self.y = np.zeros([500,9]) - self.extra

        # The window
        self.fig, self.axes  = subplots(1,2, figsize=(8, 5))

        for i in range(1):

            setattr(self, f'line{i}',Line2D([], [])) 
            self.axes[1].add_line(getattr(self,f'line{i}')) 
        for i in range(1,9):

            setattr(self, f'line{i}',Line2D([], [])) 
            self.axes[0].add_line(getattr(self,f'line{i}')) 
        
        self.line9 = Line2D([], [], color='red', alpha=0.3)
        self.line10 = Line2D([], [], color='red', marker='o', markersize=10)
        self.axes[1].add_line(self.line9) 
        self.axes[1].add_line(self.line10) 
        self.labels = [f'Channel {chan}' for chan in range (1,9)]
        self.axes[0].set_xlim(0, 500)
        
        self.axes[0].set_ylim(-self.scale*9, -0)
        self.axes[0].set_yticks(-self.extra[1:])
        self.axes[0].set_yticklabels(self.labels)

        self.axes[1].set_xlim(0, 500)
        self.axes[1].set_ylim(0,1.5)
        self.axes[1].set_xticks(self.timelinex)
        self.axes[1].set_xticklabels(self.timeline)
        self.axes[1].set_yticks([])
        self.axes[1].set_yticks([], minor=True)
        
        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = 50,repeat=True, blit = True)
        

    def new_frame_seq(self):
        return iter(range(self.n.size))

    def _init_draw(self):
        for l in range(10):
            getattr(self,f'line{l}').set_data([], [])

    def addData(self, value):
        self.addedData.put(value)
        
    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.abc += 1
            print(str(self.abc))
            TimedAnimation._stop(self)
            pass
    def update_amp(self, new_val):
        self.amplitude = new_val
        self.cue_line = np.hstack([np.zeros(540), np.linspace(0, new_val, 40), np.ones(200) * new_val,np.linspace( new_val, 0,40)  ]) # 1sec = 20

    def set_line(self, idx):
        getattr(self, f"line{idx}").set_data( self.n, range(2000))
    
    def moving_average(self, a, n=3):
        ret = np.cumsum(a, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n
    
    def _draw_frame(self, framedata):
        try:
            new_data = self.addedData.get_nowait()
            self.y = np.roll(self.y,-1,0)
            self.cue_line = np.roll(self.cue_line,-1)
            self.y[-1,:] = new_data
            self.y[-1,:] -= self.extra
            plottingdata = self.moving_average(self.y[:,0], 15)

        except Exception as e:
            print("Error:", type(e),e)
        
       
        try:
            self.line0.set_data(range(400),plottingdata[86:])
            for i in range (1,9): 
                getattr(self, f"line{i}").set_data(range(500),self.y[:,i])
            self.line9.set_data(range(500), self.cue_line[:500])
            self.line10.set_data(400,plottingdata[-1])
            self.axes[1].set_ylim(-0.01, self.amplitude * 2)
            self.axes[1].set_yticks([], minor=True)
            self._drawn_artists = [getattr(self, f"line{i}") for i in range(11)]
        except Exception as e:
            print("Error after get data",e)