"""
gatefilter.py
"""

# Load the needed packages
from PyQt4 import QtGui, QtCore
from functools import partial
import os
import numpy as np
import pyart
import time

from .. import core
from ..components import RadarDisplay
common = core.common


class GateFilter(core.Component):
    '''
    Interface for executing :py:func:`pyart.correct.GateFilter`.
    '''

    Vradar = None  #: see :ref:`shared_variable`
    Vgatefilter = None  #: see :ref:`shared_variable`

    @classmethod
    def guiStart(self, parent=None):
        '''Graphical interface for starting this class.'''
        kwargs, independent = \
            common._SimplePluginStart("GateFilter").startDisplay()
        kwargs['parent'] = parent
        return self(**kwargs), independent

    def __init__(self, Vradar=None, Vgatefilter=None,
                 name="GateFilter", parent=None):
        '''Initialize the class to create the interface.

        Parameters
        ----------
        [Optional]
        Vradar : :py:class:`~artview.core.core.Variable` instance
            Radar signal variable.
            A value of None initializes an empty Variable.
        Vgatefilter : :py:class:`~artview.core.core.Variable` instance
            GateFilter signal variable.
            A value of None initializes an empty Variable.
        name : string
            GateFilter instance window name.
        parent : PyQt instance
            Parent instance to associate to this class.
            If None, then Qt owns, otherwise associated w/ parent PyQt instance
        '''
        super(GateFilter, self).__init__(name=name, parent=parent)
        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtGui.QGridLayout(self.central_widget)

        # Set up signal, so that DISPLAY can react to
        # changes in radar or gatefilter shared variables
        if Vradar is None:
            self.Vradar = core.Variable(None)
        else:
            self.Vradar = Vradar

        if Vgatefilter is None:
            self.Vgatefilter = core.Variable(None)
        else:
            self.Vgatefilter = Vgatefilter

        self.sharedVariables = {"Vradar": None,
                                "Vgatefilter": None,}
        # Connect the components
        self.connectAllVariables()
        self.field = None

        self.operators = {"=": "exclude_equal",
                          "!=": "exclude_not_equal",
                          "<": "exclude_below",
                          "<=": "exclude_below",
                          ">": "exclude_above",
                          ">=": "exclude_above",
                          "inside": "exclude_inside",
                          "outside": "exclude_outside",
                          }

        self.generalLayout = QtGui.QVBoxLayout()
        # Set the Variable layout
        self.generalLayout.addWidget(self.createVarUI())
        self.generalLayout.addWidget(self.createFilterBox())
        self.generalLayout.addWidget(self.createButtonUI())

        self.layout.addLayout(self.generalLayout, 0, 0, 1, 2)

        self.show()

    ######################
    ##  Layout Methods  ##
    ######################

    def createVarUI(self):
        '''
        Mount the Variable layout.
        User may select another Display
        '''
        groupBox = QtGui.QGroupBox("Variable Input")
        gBox_layout = QtGui.QGridLayout()

        self.dispCombo = QtGui.QComboBox()
        gBox_layout.addWidget(QtGui.QLabel("Select Display Link"), 0, 0)
        gBox_layout.addWidget(self.dispCombo, 0, 1, 1, 1)

        self.DispChoiceList = []
        self.components = core.componentsList
        for component in self.components:
            if "Vradar" in component.sharedVariables.keys():
                if "Vgatefilter" in component.sharedVariables.keys():
                    self.dispCombo.addItem(component.name)
                    self.DispChoiceList.append(component)
        self.dispCombo.setCurrentIndex(0)

        self.chooseDisplay()
        groupBox.setLayout(gBox_layout)

        return groupBox

    def createButtonUI(self):
        '''Mount the Action layout.'''
        groupBox = QtGui.QGroupBox("Select Action")
        gBox_layout = QtGui.QGridLayout()

        self.helpButton = QtGui.QPushButton("Help")
        self.helpButton.clicked.connect(self.displayHelp)
        gBox_layout.addWidget(self.helpButton, 0, 0, 1, 1)

        self.scriptButton = QtGui.QPushButton("Show Script")
        self.scriptButton.clicked.connect(self.showScript)
        self.scriptButton.setToolTip('Display relevant python script')
        gBox_layout.addWidget(self.scriptButton, 0, 1, 1, 1)

        self.scriptButton = QtGui.QPushButton("Save File")
        self.scriptButton.clicked.connect(self.saveRadar)
        self.scriptButton.setToolTip('Save cfRadial data file')
        gBox_layout.addWidget(self.scriptButton, 0, 2, 1, 1)
        
        self.restoreButton = QtGui.QPushButton("Restore to Original")
        self.restoreButton.clicked.connect(self.restoreRadar)
        self.restoreButton.setToolTip('Remove applied filters')
        gBox_layout.addWidget(self.restoreButton, 0, 3, 1, 1)

        self.filterButton = QtGui.QPushButton("Filter")
        self.filterButton.clicked.connect(self.apply_filters)
        self.filterButton.setToolTip('Execute pyart.correct.GateFilter')
        gBox_layout.addWidget(self.filterButton, 0, 4, 1, 1)

        groupBox.setLayout(gBox_layout)

        return groupBox

    def createFilterBox(self):
        '''Mount options layout.'''
        # Create lists for each column
        chkactive =[]
        fldlab = []
        operator = []
        loval = []
        hival =[]

        groupBox = QtGui.QGroupBox("Filter Design - Exclude via the following statements")
		#groupBox.setFlat(True)
        gBox_layout = QtGui.QGridLayout()

        gBox_layout.addWidget(QtGui.QLabel("Activate\nFilter"), 0, 0, 1, 1)
        gBox_layout.addWidget(QtGui.QLabel("Variable"), 0, 1, 1, 1)
        gBox_layout.addWidget(QtGui.QLabel("Operation"), 0, 2, 1, 1)
        gBox_layout.addWidget(QtGui.QLabel("Value 1"), 0, 3, 1, 1)
        gBox_layout.addWidget(QtGui.QLabel("Value 2\nFor outside/inside"), 0, 4, 1, 1)

        self.fieldfilter = {}

        for nn, field in enumerate(self.Vradar.value.fields.keys()):
            chkactive.append(QtGui.QCheckBox())
            chkactive[nn].setChecked(False)
            fldlab.append(QtGui.QLabel(field))
            loval.append(QtGui.QLineEdit(""))
            hival.append(QtGui.QLineEdit(""))
            operator.append(self.set_operator_menu())

            gBox_layout.addWidget(chkactive[nn], nn+1, 0, 1, 1)
            gBox_layout.addWidget(fldlab[nn], nn+1, 1, 1, 1)
            gBox_layout.addWidget(operator[nn], nn+1, 2, 1, 1)
            gBox_layout.addWidget(loval[nn], nn+1, 3, 1, 1)
            gBox_layout.addWidget(hival[nn], nn+1, 4, 1, 1)

        groupBox.setLayout(gBox_layout)

        self.fieldfilter["check_active"] = chkactive
        self.fieldfilter["field"] = fldlab
        self.fieldfilter["operator"] = operator
        self.fieldfilter["low_value"] = loval
        self.fieldfilter["high_value"] = hival

#         for index, chk in enumerate(self.fieldfilter["check_active"]):
#             if chk.isChecked():
#                 if (self.fieldfilter["operator"] == 'outside' or 
#                    self.fieldfilter["operator"] == 'inside'):
#                     self.fieldfilter["high_value"].setText(' ')
#                     self.fieldfilter["high_value"].setReadOnly(True)
            
        return groupBox

    #########################
    ##  Selection Methods  ##
    #########################

    def chooseDisplay(self):
        '''Get Radar with :py:class:`~artview.core.VariableChoose`.'''
        selection = self.dispCombo.currentIndex()
        Vradar = getattr(self.DispChoiceList[selection], str("Vradar"))
        Vgatefilter = getattr(self.DispChoiceList[selection], str("Vgatefilter"))
        
        self.dispCombo.setCurrentIndex(selection)
        
        self.Vradar = Vradar
        self.Vgatefilter = Vgatefilter

    def displayHelp(self):
        '''Display Py-Art's docstring for help.'''
        text = "**Using the GateFilter window**\n"
        text += "Choose a filter:\n"
        text += "  1. Select an operation and value(s) to exclude.\n"
        text += "       Notes: 'outside' masks values less than 'Value 1' and greater than 'Value 2.'\n"
        text += "              'inside' masks values greater than 'Value 1' and less than 'Value 2.'\n"
        text += "              For other operations only 'Value 1 is used.\n"
        text += "  2. Check the 'Activate Filter' box to apply the filter.\n"
        text += "  3. Click the 'Filter' button.\n\n"
        text += "Change Radar variables:\n"
        text += "  Click the 'Find Variable', select variable.\n\n"
        text += "Show Python script for batching:\n"
        text += "  Click the 'Show Script' button.\n\n"
        text += "The following information is from the PyArt documentation.\n\n"
        text += "**GateFilter**\n"
        text += pyart.correct.GateFilter.__doc__
        text += "\n\n"
        text += "**GateFilter.exclude_below**\n"
        text += pyart.correct.GateFilter.exclude_below.__doc__
        common.ShowLongText(text)

    def set_operator_menu(self):
        '''Set the field operators choice.'''
        opBox = QtGui.QComboBox()
        opBox.setFocusPolicy(QtCore.Qt.NoFocus)
        opBox.setToolTip("Select filter operator.\n")
        opBox_layout = QtGui.QVBoxLayout()
        for op in self.operators.keys():
            opBox.addItem(op)
        opBox.setLayout(opBox_layout)

        return opBox

    def showScript(self):
        '''Create the output script to reproduce filtering results.'''
        text = "<b>PyArt Script Commands</b><br><br>"
        text += "<i>Warning</i>: This generated script is not complete!<br>"
        text += "The commands below are intended to be integrated for use in "
        text += "batch scripting to achieve the same results seen in the Display.<br><br>"
        text += "Just copy and paste the below commands into your script.<br><br>"
        text += "<i>Commands</i>:<br><br>"
        text += "gatefilter = pyart.correct.GateFilter(radar, exclude_based=True)<br>"

        try:
            for cmd in self.filterscript:
                text += cmd + "\n"
        except:
            common.ShowWarning("Must apply filter first.")

        common.ShowLongText(text)

    def saveRadar(self):
        '''Open a dialog box to save radar file.'''
        dirIn, fname = os.path.split(self.Vradar.value.filename)
        filename = QtGui.QFileDialog.getSaveFileName(
                self, 'Save Radar File', dirIn)
        filename = str(filename)
        if filename == '' or self.Vradar.value is None:
            return
        else:
#            self.AddCorrectedFields()
            for field in self.Vradar.value.fields.keys():
                self.Vradar.value.fields[field]['data'].mask = self.Vgatefilter.value._gate_excluded

                # **This section is a potential replacement for merging
                # if problems are found in mask later **
#                # combine the masks  (noting two Falses is a good point)
#                combine = np.ma.mask_or(self.Vradar.value.fields[field]['data'].mask, 
#                                        self.Vgatefilter.value._gate_excluded)
#                self.Vradar.value.fields[field]['data'].mask = np.ma.mask_or(combine, 
#                     self.Vradar.value.fields[field]['data'].mask)
#                self.Vradar.value.fields[field].data[:]=np.where(combine,
#                      self.Vradar.value.fields[field]['_FillValue'],
#                      self.Vradar.value.fields[field]['data'].data)

            pyart.io.write_cfradial(filename, self.Vradar.value)
            print("Saved %s"%(filename))

    def restoreRadar(self):
        '''Remove applied filters by restoring original mask'''
        for field in self.Vradar.value.fields.keys():
            self.Vradar.value.fields[field]['data'].mask = self.original_masks[field]
        self.Vgatefilter.value._gate_excluded = self.original_masks[field]
        self.NewGateFilter(self.Vgatefilter.value, True)

    def AddCorrectedFields(self):
        '''Launch a display window to show the filter application.'''
        # Add fields for each variable for filters
        for dupfield in self.filt_flds:
            data = self.Vradar.value.fields[dupfield]['data'][:]
            self.Vradar.value.add_field_like(dupfield, "corr_" + dupfield,
                                         data, replace_existing=False)

    ######################
    ##  Filter Methods  ##
    ######################

    def NewGateFilter(self, value, strong):
        '''
        Slot for value change of
        :py:class:`Vgatefilter <artview.core.core.Variable>`.
        '''
        self.Vgatefilter.change(value, strong)

    def apply_filters(self):
        '''Mount Options and execute
        :py:func:`~pyart.correct.GateFilter`.
        The resulting fields are added to Vradar.
        Vradar is updated, strong or weak depending on overwriting old fields.
        '''
        # Test radar
        if self.Vradar.value is None:
            common.ShowWarning("Radar is None, can not perform filtering.")
            return

        # Retain the original masks
        self.original_masks = {}
        for field in self.Vradar.value.fields.keys():
            self.original_masks[field] = self.Vradar.value.fields[field]['data'].mask
            print(field)
            print(np.sum(self.original_masks[field]))

        gatefilter = pyart.correct.GateFilter(self.Vradar.value, exclude_based=True)

        # Clear flags from previous filter application or instantiate if first
        args = {}
        self.filterscript = []

        # Create a list of possible filtering actions
        val2Cmds = ["inside", "outside"]
        valinc = [">=", "<="]

        # Initial point for timing
        t0 = time.time()

        # Get a list of field to apply the filters
        self.filt_flds = []

        pyarterr = "Py-ART fails with following error\n\n"
        # Execute chosen filters
        print("Applying filters ..")
        NoChecks = True
        for index, chk in enumerate(self.fieldfilter["check_active"]):
            if chk.isChecked():
                NoChecks = False
                field = str(self.fieldfilter["field"][index].text())
                operator = str(self.fieldfilter["operator"][index].currentText())
                val1 = self.fieldfilter["low_value"][index].text()
                val2 = self.fieldfilter["high_value"][index].text()

                print("%s checked, %s, v1 = %s, v2 = %s"%(
                field, self.operators[operator], val1, val2))

                # Create the command to be issued for filtering
                # Try that command and return error if fail

                # If the operator takes val1 and val2
                if operator in val2Cmds:
                    filtercmd = "gatefilter.%s(%s, %s, %s)"%(
                      self.operators[operator], field, val1, val2)
                    if operator == "inside":
                        try:
                            gatefilter.exclude_inside(
                             field, float(val1), float(val2))
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                    else:
                        try:
                            gatefilter.exclude_outside(
                             field, float(val1), float(val2))
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                # If the operators are inclusive of val1
                elif operator in valinc:
                    filtercmd = "gatefilter.%s(%s, %s, inclusive=True)"%(
                      self.operators[operator], field, val1)
                    if operator == "<=":
                        try:
                            gatefilter.exclude_below(
                              field, float(val1), inclusive=True)
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                    elif operator == ">=":
                        try:
                            gatefilter.exclude_above(
                              field, float(val1), inclusive=True)
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                # If the operators are exclusive of val1
                else:
                    filtercmd = "gatefilter.%s(%s, %s, inclusive=False)"%(
                      self.operators[operator], field, val1)
                    if operator == "=":
                        try:
                            gatefilter.exclude_equal(
                              field, float(val1))
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                    elif operator == "!=":
                        try:
                            gatefilter.exclude_not_equal(
                              field, float(val1))
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                    elif operator == "<":
                        try:
                            gatefilter.exclude_below(
                              field, float(val1), inclusive=False)
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)
                    elif operator == ">":
                        try:
                            gatefilter.exclude_above(
                              field, float(val1), inclusive=False)
                        except:
                            import traceback
                            error = traceback.format_exc()
                            common.ShowLongText(pyarterr + error)

                self.filterscript.append(filtercmd)

        print(("Filtering took %fs" % (time.time()-t0)))
        # If no filters were applied issue warning
        if NoChecks:
            common.ShowWarning("Please Activate Filter(s)")
            return

        strong_update = True
        # add fields and update
        self.NewGateFilter(gatefilter, strong_update)

    def _clearLayout(self, layout):
        '''recursively remove items from layout.'''
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self._clearLayout(item.layout())

_plugins = [GateFilter]


class MyQCheckBox(QtGui.QCheckBox):

    def __init__(self, *args, **kwargs):
        QtGui.QCheckBox.__init__(self, *args, **kwargs)        
        self.is_modifiable = True
        self.clicked.connect( self.value_change_slot )

    def value_change_slot(self): 
        if self.isChecked():
            self.setChecked(self.is_modifiable)
        else:
            self.setChecked(not self.is_modifiable)            

    def setModifiable(self, flag):
        self.is_modifiable = flag            

    def isModifiable(self):
        return self.is_modifiable