"""
cmap_value.py
"""

# Load the needed packages
import csv
import pyart
import numpy as np
import os
#import sys
#sys.path.append('artview')
from .. import core


TEST_OPTION = 1

class Rotation(core.Component):

    csvdata = np.genfromtxt(os.path.dirname(__file__) + '/data_1.csv',
                            dtype=float,
                            delimiter=',')
    datapt =0

    @classmethod
    def guiStart(self, parent=None):
        kwargs, independent = core.common._SimplePluginStart(
                                            "Rotation").startDisplay()
        kwargs['parent'] = parent
        return self(**kwargs), independent

#    def xyz(self):
#        with open(os.path.dirname(__file__) + '/data_1.csv', 'rb') as csvfile:
#            spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
#            x=0
#            for row in spamreader:
#               if(x!=0):
#                   self.csvdata =row[0]
#               else:
#                   x=1

        #print "------------------------"+self.csvdata
#        print self.csvdata[0]

    def __init__(self, name="Rotation", parent=None):
        '''
        make test radar for animation
        '''
        super(Rotation, self).__init__(name=name, parent=parent)
        #self.xyz()

        self.central_widget = core.QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = core.QtGui.QGridLayout(self.central_widget)
        self.button = core.QtGui.QPushButton("Start/Stop")
        self.button.clicked.connect(self.start_stop)
        self.layout.addWidget(self.button, 0, 0)
        self.running = False

        if TEST_OPTION == 1:
            radar = pyart.testing.make_empty_ppi_radar(1017, 360, 1)
            radar.fields['reflectivity'] = {'data': np.zeros((360,1017))}
            radar.fields['reflectivity'] = {}
        elif TEST_OPTION == 2:
            radar = pyart.testing.make_empty_ppi_radar(1017, 1340, 1)
            radar.fields['reflectivity'] = {'data': np.zeros((1340,1017))}
            radar.azimuth['data'] *= 360./1340

        radar.range['data'] = 26.5 * radar.range['data']
        self.field = list(radar.fields.keys())[0]
        radar.fields[self.field]['data']=0*radar.fields[self.field]['data']
        self.seed=90

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
        #data=(np.sin(np.arange(50)*0.1+self.seed/50.)+1)*25
#        self.datapt = self.datapt+1
#        data=self.csvdata[self.datapt]
#        print self.csvdata
#        print data
#        if(self.datapt>=360):
#            self.datapt=0

        if TEST_OPTION == 1:
            ray = np.mod(self.seed,360)
        elif TEST_OPTION == 2:
            ray = np.mod(self.seed,1340)
        self.Vradar.value.fields[self.field]['data'][ray] = self.csvdata[self.seed]
        self.seed = self.seed + 1
        if self.seed >= 1340:
            self.seed = 0
        self.Vradar.update()

_plugins = [Rotation]

