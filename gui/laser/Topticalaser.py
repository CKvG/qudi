# -*- coding: utf-8 -*-

"""
This file contains a gui for the laser controller logic.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import numpy as np
import os
import pyqtgraph as pg
import time

from core.connector import Connector
from gui.colordefs import QudiPalettePale as palette
from gui.guibase import GUIBase
from interface.Toptica_laser_interface import ControlMode, ShutterState, LaserState, ChannelSelect, AdvancedFeatureSelect
from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import uic


class TimeAxisItem(pg.AxisItem):
    """ pyqtgraph AxisItem that shows a HH:MM:SS timestamp on ticks.
        X-Axis must be formatted as (floating point) Unix time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        """ Hours:Minutes:Seconds string from float unix timestamp. """
        return [time.strftime("%H:%M:%S", time.localtime(value)) for value in values]


class LaserWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_Topticalaser.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()


class TopticaLaserGUI(GUIBase):
    """ FIXME: Please document
    """

    ## declare connectors
    laserlogic = Connector(interface='TopticaLaserLogic')

    sigLaser = QtCore.Signal(bool)
    #sigShutter = QtCore.Signal(bool)

    sigChannel = QtCore.Signal(ChannelSelect)
    sigPowerCh1 = QtCore.Signal(float)
    sigPowerCh2 = QtCore.Signal(float)

    sigAutoPulse = QtCore.Signal(bool)
    sigFrequ = QtCore.Signal(float)
    sigDuty = QtCore.Signal(float)
    sigPeriod = QtCore.Signal(int)
    sigWidth = QtCore.Signal(int)

    sigAdvancedFeatures = QtCore.Signal(AdvancedFeatureSelect)
    sigFineA = QtCore.Signal(int)
    sigFineB = QtCore.Signal(int)

    #sigCurrent = QtCore.Signal(float)
    sigCtrlMode = QtCore.Signal(ControlMode)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.
        """
        self._laser_logic = self.laserlogic()

        #####################
        # Configuring the dock widgets
        # Use the inherited class 'CounterMainWindow' to create the GUI window
        self._mw = LaserWindow()

        # Setup dock widgets
        self._mw.setDockNestingEnabled(True)
        self._mw.actionReset_View.triggered.connect(self.restoreDefaultView)

        # set up plot
        self._mw.plotWidget = pg.PlotWidget(
            axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self._mw.pwContainer.layout().addWidget(self._mw.plotWidget)

        plot1 = self._mw.plotWidget.getPlotItem()
        plot1.setLabel('left', 'power', units='W', color=palette.c1.name())
        plot1.setLabel('bottom', 'Time', units=None)
        plot1.setLabel('right', 'Temperature', units='°C', color=palette.c3.name())

        plot2 = pg.ViewBox()
        plot1.scene().addItem(plot2)
        plot1.getAxis('right').linkToView(plot2)
        plot2.setXLink(plot1)

        self.curves = {}
        colorlist = (palette.c2, palette.c3, palette.c4, palette.c5, palette.c6)
        i = 0
        for name in self._laser_logic.data:
            if name != 'time':
                curve = pg.PlotDataItem()
                if name == 'power':
                    curve.setPen(palette.c1)
                    plot1.addItem(curve)
                else:
                    curve.setPen(colorlist[(2*i) % len(colorlist)])
                    plot2.addItem(curve)
                self.curves[name] = curve
                i += 1

        self.plot1 = plot1
        self.plot2 = plot2
        self.updateViews()
        self.plot1.vb.sigResized.connect(self.updateViews)

        self.configureValues()
        self.updateButtonsEnabled()
        self._mw.laserButton.setStyleSheet('\
                                                background-color: grey;')
        self._mw.laserButton.clicked.connect(self.changeLaserState)

        self.sigLaser.connect(self._laser_logic.set_laser_state)
        self.sigPowerCh1.connect(self._laser_logic.set_power_ch1)
        self.sigPowerCh2.connect(self._laser_logic.set_power_ch2)
        self._mw.channel1CheckBox.stateChanged.connect(lambda:self.updateChannel())
        self._mw.channel2CheckBox.stateChanged.connect(lambda:self.updateChannel())
        #TODO: self.sigChannel.connect(self._laser_logic.set_channel)
        self._mw.horizontalSliderCh1.valueChanged.connect(self.updateFromSlider_ch1)
        self._mw.horizontalSliderCh2.valueChanged.connect(self.updateFromSlider_ch2)


        #TODO
        self._mw.horizontalSliderFrequ.valueChanged.connect(self.updateFromSlider_Frequ)
        self._mw.horizontalSliderDuty.valueChanged.connect(self.updateFromSlider_Duty)
        self._mw.horizontalSliderPeriod.valueChanged.connect(self.updateFromSlider_Period)
        self._mw.horizontalSliderWidth.valueChanged.connect(self.updateFromSlider_Width)
        self.sigFrequ.connect(self._laser_logic.set_autopulse_freq)
        self.sigDuty.connect(self._laser_logic.set_autopulse_duty)
        self.sigPeriod.connect(self._laser_logic.set_autopulse_per)
        self.sigWidth.connect(self._laser_logic.set_autopulse_width)
        self._mw.autopulseCheckBox.stateChanged.connect(lambda:self.updateAutoPulse())
        self.sigAutoPulse.connect(self._laser_logic.set_autopulse)


        self._mw.setValueCh1.valueChanged.connect(self.updateFromSpinBox_Ch1)
        self._mw.setValueCh2.valueChanged.connect(self.updateFromSpinBox_Ch2)

        self._mw.setValueFrequ.valueChanged.connect(self.updateFromSpinBox_Frequ)
        self._mw.setValueDuty.valueChanged.connect(self.updateFromSpinBox_Duty)
        self._mw.setValuePeriod.valueChanged.connect(self.updateFromSpinBox_Period)
        self._mw.setValueWidth.valueChanged.connect(self.updateFromSpinBox_Width)

        self._mw.setParamAF.currentIndexChanged.connect(self.updateAdvancedFeatures_View)

        self._mw.horizontalSliderFineA.valueChanged.connect(self.updateFromSlider_FineA)
        self._mw.horizontalSliderFineB.valueChanged.connect(self.updateFromSlider_FineB)
        self._mw.setValueFineA.valueChanged.connect(self.updateFromSpinBox_FineA)
        self._mw.setValueFineB.valueChanged.connect(self.updateFromSpinBox_FineB)

        self._mw.fineCheckBox.stateChanged.connect(lambda:self.updateAdvancedFeatures())
        self.sigAdvancedFeatures.connect(self._laser_logic.set_advanced_features)

        self._mw.groupBoxAP.toggled.connect(lambda: self.updateViews_fromAutoPulse())


        self._laser_logic.sigUpdate.connect(self.updateGui)

    def on_deactivate(self):
        """ Deactivate the module properly.
        """
        self.changeLaserState(False)
        self._mw.close()

    def show(self):
        """Make window visible and put it above all other windows.
        """
        QtWidgets.QMainWindow.show(self._mw)
        self._mw.activateWindow()
        self._mw.raise_()

    def restoreDefaultView(self):
        """ Restore the arrangement of DockWidgets to the default
        """
        # Show any hidden dock widgets
        self._mw.adjustDockWidget.show()
        self._mw.plotDockWidget.show()

        # re-dock any floating dock widgets
        self._mw.adjustDockWidget.setFloating(False)
        self._mw.plotDockWidget.setFloating(False)

        # Arrange docks widgets
        self._mw.addDockWidget(QtCore.Qt.DockWidgetArea(1), self._mw.adjustDockWidget)
        self._mw.addDockWidget(QtCore.Qt.DockWidgetArea(2), self._mw.plotDockWidget)

    @QtCore.Slot()
    def updateConnectionBox(self):
        """"""
        portlist = self._laser_logic.getOpenPorts
        self._mw.connectionBox.clear()
        self._mw.connectionBox.addItems(portlist)


    def configureValues(self):
        """
        Returns
        -------
        None.
        """
        lpr = self._laser_logic.laser_power_range
        self._mw.horizontalSliderCh1.setMinimum(int(lpr[0]))
        self._mw.horizontalSliderCh1.setMaximum(int(lpr[1]*1000))
        self._mw.horizontalSliderCh1.setTickInterval(1)
        self._mw.setValueCh1.setRange(lpr[0], lpr[1])

        self._mw.horizontalSliderCh2.setMinimum(int(lpr[0]))
        self._mw.horizontalSliderCh2.setMaximum(int(lpr[1]*1000))
        self._mw.horizontalSliderCh2.setTickInterval(1)
        self._mw.setValueCh2.setRange(lpr[0], lpr[1])

    @QtCore.Slot()
    def updateViews(self):
        """ Keep plot views for left and right axis identical when resizing the plot widget. """
        # view has resized; update auxiliary views to match
        self.plot2.setGeometry(self.plot1.vb.sceneBoundingRect())

        # need to re-update linked axes since this was called incorrectly while views had different
        # shapes. (probably this should be handled in ViewBox.resizeEvent)
        self.plot2.linkedViewChanged(self.plot1.vb, self.plot2.XAxis)

    @QtCore.Slot(bool)
    def changeLaserState(self, on):
        """ Disable laser power button and give logic signal.
            Logic reaction to that signal will enable the button again.
        """
        #self._mw.laserButton.setEnabled(False)
        self.sigLaser.emit(on)

    # @QtCore.Slot(bool)
    # def changeShutterState(self, on):
    #     """ Disable laser shutter button and give logic signal.
    #         Logic reaction to that signal will enable the button again.
    #     """
    #     self._mw.shutterButton.setEnabled(False)
    #     self.sigShutter.emit(on)

    @QtCore.Slot()
    def updateButtonsEnabled(self):
        """ Logic told us to update our button states, so set the buttons accordingly. """
        #self._mw.laserButton.setEnabled(self._laser_logic.laser_can_turn_on)# TODO
        if self._laser_logic.laser_state == LaserState.ON:
            self._mw.laserButton.setText('Laser: ON')
            self._mw.laserButton.setChecked(True)
            self._mw.laserButton.setStyleSheet('\
                                                background-color: green;')

        elif self._laser_logic.laser_state == LaserState.OFF:
            self._mw.laserButton.setText('Laser: OFF')
            self._mw.laserButton.setChecked(False)
            self._mw.laserButton.setStyleSheet('\
                                                background-color: grey;')
        elif self._laser_logic.laser_state == LaserState.LOCKED:
            self._mw.laserButton.setText('INTERLOCK')
        else:
            self._mw.laserButton.setText('Laser: ?')

        # self._mw.channel1CheckBox.setEnabled(True)
        # self._mw.channel2CheckBox.setEnabled(True)
        # if self._mw.channel1CheckBox.isChecked():
        #     self._mw.hLayoutCh1.setEnabled(True)
        #     self._mw.horizontalSliderCh1.setEnabled(True)
        # else:
        #     self._mw.hLayoutCh1.setEnabled(False)
        #     self._mw.horizontalSliderCh1.setEnabled(False)

        # if self._mw.channel2CheckBox.isChecked():
        #     self._mw.groupBoxAP.setEnabled(False)
        #     self._mw.hLayoutCh2.setEnabled(True)
        #     self._mw.horizontalSliderCh2.setEnabled(True)
        # else:
        #     self._mw.groupBoxAP.setEnabled(True)
        #     self._mw.hLayoutCh2.setEnabled(False)
        #     self._mw.horizontalSliderCh2.setEnabled(False)

    @QtCore.Slot()
    def updateGui(self):
        """ Update labels, the plot and button states with new data. """
        #self._mw.currentLabel.setText(
            #'{0:6.3f} {1}'.format(
               # self._laser_logic.laser_current,
                #self._laser_logic.laser_current_unit))
        if self._mw.channel1Label.isEnabled():
            self._mw.channel1Label.setText('{0:9.4f} mW'.format(self._laser_logic.laser_power)) #TODO !
        if self._mw.channel2Label.isEnabled():
            self._mw.channel2Label.setText('{0:9.4f} mW'.format(self._laser_logic.laser_power)) #TODO !
        #self._mw.chInfoLabel.setText(self._laser_logic.channel_info)
        self._mw.autopulseLabel.setText('Autopulse feature: {0}'.format(self._laser_logic.laser_autopulseInfo))
        self._mw.fineLabel.setText('FINE feature: {0}'.format(self._laser_logic.laser_fineInfo))
        self._mw.TempValue.setText('{0:3.2f} °C'.format(self._laser_logic.laser_temps["Diode"]))

        self._mw.extraLabel.setText(self._laser_logic.laser_extra)
        self.updateButtonsEnabled()
        for name, curve in self.curves.items():
            curve.setData(x=self._laser_logic.data['time'], y=self._laser_logic.data[name])


    @QtCore.Slot(QtWidgets.QAbstractButton)
    def updateChannel(self):
        """ Update visibility of controls due to selected channel configuration. """
        # cur = self._mw.currentRadioButton.isChecked() and self._mw.currentRadioButton.isEnabled()
        self.sigCtrlMode.emit(ControlMode.POWER)
        ch1 = self._mw.channel1CheckBox.isChecked()
        ch2 = self._mw.channel2CheckBox.isChecked()
        lpr = self._laser_logic.laser_power_range
        if ch1 and not ch2:
            self._mw.channel2Label.setEnabled(False)
            self._mw.horizontalSliderCh2.setEnabled(False)
            self._mw.setValueCh2.setEnabled(False)
            self._mw.channel1Label.setEnabled(True)
            self._mw.horizontalSliderCh1.setEnabled(True)
            self._mw.setValueCh1.setEnabled(True)
            self._mw.groupBoxAP.setEnabled(True)
            self._mw.laserButton.setEnabled(True)
            self.sigChannel.emit(ChannelSelect.CHANNEL1)
        elif ch2 and not ch1:
            self._mw.channel1Label.setEnabled(False)
            self._mw.horizontalSliderCh1.setEnabled(False)
            self._mw.setValueCh1.setEnabled(False)
            self._mw.channel2Label.setEnabled(True)
            self._mw.horizontalSliderCh2.setEnabled(True)
            self._mw.setValueCh2.setEnabled(True)
            self._mw.groupBoxAP.setEnabled(False)
            self._mw.laserButton.setEnabled(True)
            self.sigChannel.emit(ChannelSelect.CHANNEL2)
        elif ch1 and ch2:
            self.sigCtrlMode.emit(ControlMode.POWER)# TODO
            self._mw.groupBoxAP.setEnabled(False)
            self._mw.channel1Label.setEnabled(True)
            self._mw.horizontalSliderCh1.setEnabled(True)
            self._mw.setValueCh1.setEnabled(True)
            self._mw.channel2Label.setEnabled(True)
            self._mw.horizontalSliderCh2.setEnabled(True)
            self._mw.setValueCh2.setEnabled(True)
            self._mw.laserButton.setEnabled(True)
            self.sigChannel.emit(ChannelSelect.BOTH)
        else:
            self._mw.groupBoxAP.setEnabled(True)
            self._mw.channel1Label.setEnabled(False)
            self._mw.horizontalSliderCh1.setEnabled(False)
            self._mw.setValueCh1.setEnabled(False)
            if self._mw.groupBoxAP.isChecked():
                self._mw.channel2Label.setEnabled(True)
                self._mw.horizontalSliderCh2.setEnabled(True)
                self._mw.setValueCh2.setEnabled(True)
                self._mw.laserButton.setEnabled(True)
            else:
                self._mw.channel2Label.setEnabled(False)
                self._mw.horizontalSliderCh2.setEnabled(False)
                self._mw.setValueCh2.setEnabled(False)
                self._mw.laserButton.setEnabled(False)
            self.sigChannel.emit(ChannelSelect.NONE)
            #self.log.error('How did you mess up the radio button group?')

    @QtCore.Slot()
    def updateViews_fromAutoPulse(self):
        if self._mw.groupBoxAP.isChecked():
            #self._mw.groupBoxAP.setEnabled(True)
            #self._mw.channel1Label.setEnabled(True)
            #self._mw.horizontalSliderCh1.setEnabled(True)
            #self._mw.setValueCh1.setEnabled(True)

            self._mw.channel2CheckBox.setChecked(False)
            self._mw.channel2CheckBox.setEnabled(False)
            self._mw.channel2Label.setEnabled(True)
            self._mw.horizontalSliderCh2.setEnabled(True)
            self._mw.setValueCh2.setEnabled(True)
            self._mw.laserButton.setEnabled(True)

        else:
            #self._mw.groupBoxAP.setEnabled(True)
            #self._mw.channel1Label.setEnabled(True)
            #self._mw.horizontalSliderCh1.setEnabled(True)
            #self._mw.setValueCh1.setEnabled(True)

            self._mw.channel2CheckBox.setEnabled(True)
            self._mw.laserButton.setEnabled(False)
            self._mw.channel2Label.setEnabled(False)
            self._mw.horizontalSliderCh2.setEnabled(False)
            self._mw.setValueCh2.setEnabled(False)

            if self._mw.channel2CheckBox.isChecked():
                self._mw.channel2Label.setEnabled(True)
                self._mw.horizontalSliderCh2.setEnabled(True)
                self._mw.setValueCh2.setEnabled(True)
            else:
                self._mw.channel2Label.setEnabled(False)
                self._mw.horizontalSliderCh2.setEnabled(False)
                self._mw.setValueCh2.setEnabled(False)




    @QtCore.Slot()
    def updateFromSpinBox_Ch1(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderCh1.setValue(self._mw.setValueCh1.value()*1000)
        ch1 = self._mw.channel1CheckBox.isChecked()
        if ch1:
            self.sigPowerCh1.emit(self._mw.setValueCh1.value())

    @QtCore.Slot()
    def updateFromSpinBox_Ch2(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderCh2.setValue(self._mw.setValueCh2.value()*1000)
        ch2 = self._mw.channel2CheckBox.isChecked()
        if ch2:
            self.sigPowerCh2.emit(self._mw.setValueCh2.value())

    @QtCore.Slot()
    def updateFromSlider_ch1(self):
        """ The user has changed the slider, update all other values from that. """
        ch1 = self._mw.channel1CheckBox.isChecked()
        if ch1:
            self._mw.setValueCh1.setValue(self._mw.horizontalSliderCh1.value() / 1000)
            self.sigPowerCh1.emit(self._mw.horizontalSliderCh1.value() / 1000)

    @QtCore.Slot()
    def updateFromSlider_ch2(self):
        """ The user has changed the slider, update all other values from that. """
        ch2 = self._mw.channel2CheckBox.isChecked()
        if ch2:
            self._mw.setValueCh2.setValue(self._mw.horizontalSliderCh2.value() / 1000)
            self.sigPowerCh2.emit(self._mw.horizontalSliderCh2.value() / 1000)


    @QtCore.Slot()
    def updateAutoPulse(self):
        """"""
        if self._mw.autopulseCheckBox.isChecked():
            if self._mw.setValueFrequ.value() < 10.0:
                self.sigPeriod.emit(self._mw.setValuePeriod.value())
            else:
                self.sigFrequ.emit(self._mw.setValueFrequ.value())
            self.sigDuty.emit(self._mw.setValueDuty.value())
            #self.sigWidth.emit(self._mw.setValueWidth.value())
            self._mw.groupBox_APValues.setEnabled(False)
            self.sigAutoPulse.emit(True)
        else:
            self._mw.groupBox_APValues.setEnabled(True)
            self.sigAutoPulse.emit(False)


    @QtCore.Slot()
    def updateFromSpinBox_Frequ(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderFrequ.setValue(int(self._mw.setValueFrequ.value()*1000))


    @QtCore.Slot()
    def updateFromSpinBox_Duty(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderDuty.setValue(int(self._mw.setValueDuty.value()*10))

    @QtCore.Slot()
    def updateFromSpinBox_Period(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderPeriod.setValue(self._mw.setValuePeriod.value())

    @QtCore.Slot()
    def updateFromSpinBox_Width(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderWidth.setValue(self._mw.setValueWidth.value())

    @QtCore.Slot()
    def updateFromSlider_Frequ(self):
        """ The user has changed the slider, update all other values from that. """
        self._mw.setValueFrequ.setValue(self._mw.horizontalSliderFrequ.value() / 1000)
        self._mw.setValuePeriod.setValue((1000/(self._mw.setValueFrequ.value())))
        self._mw.setValueWidth.setValue((1/(self._mw.setValueFrequ.value()) * self._mw.setValueDuty.value()/1000))

    @QtCore.Slot()
    def updateFromSlider_Duty(self):
        """ The user has changed the slider, update all other values from that. """
        self._mw.setValueDuty.setValue(self._mw.horizontalSliderDuty.value() / 10)
        self._mw.setValueWidth.setValue((self._mw.setValueDuty.value()/100) * (self._mw.setValuePeriod.value()))

    @QtCore.Slot()
    def updateFromSlider_Period(self):
        """ The user has changed the slider, update all other values from that. """
        self._mw.setValuePeriod.setValue(self._mw.horizontalSliderPeriod.value())
        self._mw.setValueWidth.setValue((self._mw.setValueDuty.value()/100) * (self._mw.setValuePeriod.value()))
        self._mw.setValueFrequ.setValue((1000/(self._mw.setValuePeriod.value())))

    @QtCore.Slot()
    def updateFromSlider_Width(self):
        """ The user has changed the slider, update all other values from that. """
        self._mw.setValueWidth.setValue(self._mw.horizontalSliderWidth.value())
        self._mw.setValueDuty.setValue(((self._mw.setValueWidth.value()) / (self._mw.setValuePeriod.value()))*100)

    @QtCore.Slot()
    def updateAdvancedFeatures_View(self):
        param = self._mw.setParamAF.currentIndex()
        if param == 0:
            self._mw.FineALabel.setEnabled(True)
            self._mw.setValueFineA.setEnabled(True)
            self._mw.horizontalSliderFineA.setEnabled(True)
            self._mw.FineBLabel.setEnabled(True)
            self._mw.setValueFineB.setEnabled(True)
            self._mw.horizontalSliderFineB.setEnabled(True)
        elif param == 1:
            #TODO: laserlogic set Skill1
            self._mw.FineALabel.setEnabled(False)
            self._mw.setValueFineA.setEnabled(False)
            self._mw.horizontalSliderFineA.setEnabled(False)
            self._mw.FineBLabel.setEnabled(False)
            self._mw.setValueFineB.setEnabled(False)
            self._mw.horizontalSliderFineB.setEnabled(False)
        # elif param == 2:
        #     #TODO: laserlogic set Skill2
        #     self._mw.FineALabel.setEnabled(False)
        #     self._mw.setValueFineA.setEnabled(False)
        #     self._mw.horizontalSliderFineA.setEnabled(False)
        #     self._mw.FineBLabel.setEnabled(False)
        #     self._mw.setValueFineB.setEnabled(False)
        #     self._mw.horizontalSliderFineB.setEnabled(False)
        #     self.sigAdvancedFeatures.emit(AdvancedFeatureSelect.SKILL2)
        else:
            self._mw.FineALabel.setEnabled(False)
            self._mw.setValueFineA.setEnabled(False)
            self._mw.horizontalSliderFineA.setEnabled(False)
            self._mw.FineBLabel.setEnabled(False)
            self._mw.setValueFineB.setEnabled(False)
            self._mw.horizontalSliderFineB.setEnabled(False)
            #self.sigAdvancedFeatures.emit(AdvancedFeatureSelect.NONE)

    @QtCore.Slot()
    def updateAdvancedFeatures(self):
        param = self._mw.setParamAF.currentIndex()
        if param == 0 & self._mw.fineCheckBox.isChecked():
            self.sigFineA.connect(self._laser_logic.set_Fine_A)
            self.sigFineB.connect(self._laser_logic.set_Fine_B)
            self.sigAdvancedFeatures.emit(AdvancedFeatureSelect.FINE)
        elif param == 1 & self._mw.fineCheckBox.isChecked():
            self.sigAdvancedFeatures.emit(AdvancedFeatureSelect.SKILL1)
        else:
            self.sigAdvancedFeatures.emit(AdvancedFeatureSelect.NONE)


    @QtCore.Slot()
    def updateFromSpinBox_FineA(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderFineA.setValue(self._mw.setValueFineA.value()*10)
        self.sigFineA.emit(self._mw.setValueFineA.value())

    @QtCore.Slot()
    def updateFromSpinBox_FineB(self):
        """ The user has changed the spinbox, update all other values from that. """
        self._mw.horizontalSliderFineB.setValue(self._mw.setValueFineB.value()*10)
        self.sigFineB.emit(self._mw.setValueFineB.value())

    @QtCore.Slot()
    def updateFromSlider_FineA(self):
        self._mw.setValueFineA.setValue(self._mw.horizontalSliderFineA.value()/10)
        self.sigFineA.emit(int(self._mw.setValueFineA.value()))

    @QtCore.Slot()
    def updateFromSlider_FineB(self):
        self._mw.setValueFineB.setValue(self._mw.horizontalSliderFineB.value()/10)
        self.sigFineB.emit(int(self._mw.setValueFineB.value()))