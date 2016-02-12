"""
cmap_value.py
"""

# Load the needed packages
import pyart
import numpy as np
from .. import core

class Rotation(core.Component):

    @classmethod
    def guiStart(self, parent=None):
        kwargs, independent = core.common._SimplePluginStart(
                                            "Rotation").startDisplay()
        kwargs['parent'] = parent
        return self(**kwargs), independent

    def __init__(self, name="Rotation", parent=None):
        '''
        make test radar for animation
        '''
        super(Rotation, self).__init__(name=name, parent=parent)


        self.central_widget = core.QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = core.QtGui.QGridLayout(self.central_widget)
        self.button = core.QtGui.QPushButton("Start/Stop")
        self.button.clicked.connect(self.start_stop)
        self.layout.addWidget(self.button, 0, 0)
        self.running = False

        radar = pyart.testing.make_target_radar()
        radar.range['data'] = 100 * radar.range['data']
        self.field = list(radar.fields.keys())[0]
        radar.fields[self.field]['data']=0*radar.fields[self.field]['data']
        self.seed=0

        self.Vradar = core.Variable(radar)

        self.sharedVariables = {"Vradar": None}
        self.connectAllVariables()

        self.timer = core.QtCore.QTimer()
        self.timer.timeout.connect(self.loop)


        self.show()

    ######################
    ##  Layout Methods  ##
    ######################

    def start_stop(self, *args):
        if self.running:
            self.running=False
            self.timer.stop()
        else:
            self.running=True
            self.timer.start(100)

    def loop(self):
        data=(np.sin(np.arange(50)*0.1+self.seed/50.)+1)*25
        ray = np.mod(self.seed,360)
        self.Vradar.value.fields[self.field]['data'][ray] = data
        self.seed=self.seed+1
        self.Vradar.update()

_plugins = [Rotation]

