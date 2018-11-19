#!/usr/bin/env python
# -*- coding: utf-8 -*-
# FrontendPlaylist.py

# Copyright (c) 2018, Richard Gerum, Achim Schilling, Hinrich Rahlfs, Matthias Streb
#
# This file is part of ASR-Setup.
#
# ASR-Setup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ASR-Setup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ASR-Setup. If not, see <http://www.gnu.org/licenses/>

import sys
from qtpy import QtCore, QtGui, QtWidgets
import copy
import numpy as np
import open_gpias.playlist.BackendPlaylist as BackendPlaylist


##DiaqlogClass to recive Schwellwert Messung Data
# This class is abled to get all needed parameter for a hearing threshold measurement
# This class can be adjusted, that means all values that have been entered earlier are still present if the dialog is opend again

class HearingThresholdDialog(QtWidgets.QDialog):

    # initializing the Dialog
    def __init__(self, parent=None):
        super(HearingThresholdDialog, self).__init__(parent)
        self.setWhatsThis(
            "Please Enter all paramters for the hearing threshold. All Fields have a tool tip. "
            "If you place the mouse arrow above them it will tell you about the Values you are allowed to enter.")

        # Using a grid layout to structure the GUI
        self.grid = QtWidgets.QGridLayout(self)
        # Label to give information what this dialog
        label = "Enter the values out of which the Playlist is generated"
        self.grid.addWidget(QtWidgets.QLabel(label), 0, 0, 1, 10)

        # Line Edit which sets the smallest frequency for which a
        # hearing threshold is tested
        self.smallestFrequency = QtWidgets.QLineEdit(self)
        self.smallestFrequency.setValidator(QtGui.QIntValidator(350, 20000))
        tip = "Enter a value between 350 and 20000. This is the lowest frequency for which a hearingthreshold is tested."
        self.smallestFrequency.setToolTip(tip)
        self.grid.addWidget(QtWidgets.QLabel("lowest frequency"), 2, 0)
        self.grid.addWidget(self.smallestFrequency, 2, 1)
        self.grid.addWidget(QtWidgets.QLabel("[Hz]"), 2, 2)

        # Line Edit which sets the highest frequency for which a
        # hearing threshold is tested
        # as the frequencies are measured in octave/halve octave or quarter
        # octave steps it often happens, that the highest frequency isn't tested
        self.highestFrequency = QtWidgets.QLineEdit(self)
        self.highestFrequency.setValidator(QtGui.QIntValidator(350, 20000))
        tip = "Enter a value between 350 and 20000. This is the highest frequency for which a hearingthreshold is tested."
        self.highestFrequency.setToolTip(tip)
        self.grid.addWidget(QtWidgets.QLabel("highest frequency"), 3, 0)
        self.grid.addWidget(self.highestFrequency, 3, 1)
        self.grid.addWidget(QtWidgets.QLabel("[Hz]"), 3, 2)

        # define the steps in which the frequency is increased
        # one octave means doubling the frequency
        self.octave = QtWidgets.QRadioButton("octave steps")
        self.halve_octave = QtWidgets.QRadioButton("half octave steps")
        self.quarter_octave = QtWidgets.QRadioButton("quarter octave steps")
        # adding buttons to a button group to connect them logically
        group_buttons = QtWidgets.QButtonGroup()
        group_buttons.addButton(self.octave, 1)
        group_buttons.addButton(self.halve_octave, 2)
        group_buttons.addButton(self.quarter_octave, 3)
        self.grid.addWidget(group_buttons.button(1), *(4, 0))
        self.grid.addWidget(group_buttons.button(2), *(5, 0))
        self.grid.addWidget(group_buttons.button(3), *(6, 0))

        # Line Edit which sets the biggest attenuation for which a
        # hearing threshold is tested
        # could be changed to be constant in future
        self.maximumPressureLevel = QtWidgets.QLineEdit(self)
        self.maximumPressureLevel.setValidator(QtGui.QIntValidator(10, 70))
        tip = "Enter a value between 10 and 70. This is the biggest noiselevel of the prestimulus. The lowest noiselevel is always no noise at all."
        self.maximumPressureLevel.setToolTip(tip)
        self.grid.addWidget(QtWidgets.QLabel("maximum noiselevel prestim"), 7, 0)
        self.grid.addWidget(self.maximumPressureLevel, 7, 1)
        self.grid.addWidget(QtWidgets.QLabel("[dB SPL]"), 7, 2)

        # attenuation level between different hearing threshold measurements
        self.stepSizePressureLevel = QtWidgets.QLineEdit(self)
        self.stepSizePressureLevel.setValidator(QtGui.QIntValidator(1, 70))
        tip = "Enter a value between 1 and 70. This is the resolution of the different noise levels."
        self.stepSizePressureLevel.setToolTip(tip)
        self.grid.addWidget(QtWidgets.QLabel("noiselevel steps prestim"), 8, 0)
        self.grid.addWidget(self.stepSizePressureLevel, 8, 1)
        self.grid.addWidget(QtWidgets.QLabel("[dB SPL]"), 8, 2)

        self.n = QtWidgets.QLineEdit(self)
        self.n.setValidator(QtGui.QIntValidator(1, 50))
        tip = "Enter a value between 1 and 50. This is the number of repeats for every measurement."
        self.n.setToolTip(tip)
        self.grid.addWidget(QtWidgets.QLabel("repetitions:"), 9, 0)
        self.grid.addWidget(self.n, 9, 1)
        self.grid.addWidget(QtWidgets.QLabel("[]"), 9, 2)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.checkAccept)
        buttons.rejected.connect(self.reject)
        self.grid.addWidget(buttons, 10, 0, 1, 3)
        self.setWindowTitle('Measurements hearing thresholds')

    # check whether all the parameters are entered correctly and handle it
    # appropriately
    # the allowed values are declared by the int validators defined in __init__
    def checkAccept(self):
        parameter = self.parameter()
        if not self.n.hasAcceptableInput():
            self.warning("repetitions is not within the allowed range")
        elif not self.smallestFrequency.hasAcceptableInput():
            self.warning("lowest frequency is not within the allowed range")
        elif not self.highestFrequency.hasAcceptableInput():
            self.warning("highest frequency is not within the allowed range")
        elif not parameter[3] >= 0:
            self.warning("There was no frequency step selected")
        elif not self.maximumPressureLevel.hasAcceptableInput():
            self.warning("maximum pre-stimulus noise level  is not within the allowed range")
        elif not self.stepSizePressureLevel.hasAcceptableInput():
            self.warning("pre-stimulus noise level steps is not within the allowed range")
        elif parameter[1] > parameter[2]:
            self.warning("lowest frequency is bigger than highest frequency")
        # if no warning occurred this dialog is accepted otherwise it wont close
        # but give a warning
        else:
            self.accept()

    # give a warning with the information in str
    def warning(self, str):
        QtWidgets.QtWidgets.QMessageBox.warning(self, 'Warning', str)

    # returns a list of the entered parameter.
    # its form is[n,smallestFreq,biggestFreq,freqFactor, maxAtten, attenSteps]
    def parameter(self):
        # frequency factor hold a value in [-1,0,1,2]
        # -1 means no radiobutton is checked
        # these buttons are used to define how big the frequency steps are
        frequenzFactor = -1
        if self.octave.isChecked():
            frequenzFactor = 0
        if self.halve_octave.isChecked():
            frequenzFactor = 1
        if self.quarter_octave.isChecked():
            frequenzFactor = 2

        # if any Value is not entered the return fails, thats why we need to
        # except an value Error
        try:
            return [int(self.n.text()),
                    int(self.smallestFrequency.text()),
                    int(self.highestFrequency.text()),
                    frequenzFactor,
                    int(self.maximumPressureLevel.text()),
                    int(self.stepSizePressureLevel.text())]
        except ValueError:
            return [self.n.text(),
                    self.smallestFrequency.text(),
                    self.highestFrequency.text(),
                    frequenzFactor,
                    self.maximumPressureLevel.text(),
                    self.stepSizePressureLevel.text()]

    # handles adjusting of the parameters
    # calls the same dialog again and returns equally to getParameter() but
    # doesn't produce a new dialog
    def adjust(self):
        result = self.exec_()
        return self, self.parameter(), result == QtWidgets.QDialog.Accepted

    # static method to create the dialog and return 
    # dialog => the dialog which gets the Values. This can be used to open the
    # same Dialog again
    # paramtertList => (see parameter())
    # accepted => a boolean which declares whether the dialog has been accepted
    # by pressing ok or closed by canceled or any other way
    @staticmethod
    def getParameter(parent=None):
        dialog = HearingThresholdDialog(parent)
        result = dialog.exec_()
        print(dialog.smallestFrequency.text())
        return dialog, dialog.parameter(), result == QtWidgets.QDialog.Accepted


##DiaqlogClass to recive Turner Measurement konfiguration
# This Dialog recieves:
#   the centers of the noiseBands which are supposed to be used
#   the width of these noisebands
#   the number of repeats
# This class can be adjusted, that means all values that have been entered
# earlier are still present if the dialog is opend again

# The dialog only returns if all values are entered within the allowed range
class TurnerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(TurnerDialog, self).__init__(parent)
        # self.setWhatsThis("hallo")
        self.setWhatsThis(
            "Please enter the paramters for the GPIAS-Measurements. Press add band middel, if you want to use a different frequency. press delete if you want to delete one.\nEnter a - befor the bandmiddel to stimulate with notched noise e.g.:-1000\nenter 0 as bandmiddel to use broad band noise")
        # gridlayout to structure th dialog
        self.grid = QtWidgets.QGridLayout(self)
        self.setLayout(self.grid)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        # Variable that saves all widgets needed for the bandmiddles
        self.setCycles = []
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        # connect buttons to accepting or rejecting function
        self.buttons.accepted.connect(self.checkAccept)
        self.buttons.rejected.connect(self.reject)
        self.grid.addWidget(self.buttons, 6, 0)

        # number of choosable bandwidths, this needs to be done, as it
        # enables the other widgets to be at the right position
        self.number_of_bandwidth = 4
        # buttons to define bandwidth around band middel(to top and bottom)
        # one oktave means doubling the frequency
        self.oktav = QtWidgets.QRadioButton("+- one octave around band middel")
        self.halbOktav = QtWidgets.QRadioButton("+- a half octave around band middel")
        self.viertelOktav = QtWidgets.QRadioButton("+- a quarter octave around band middel")
        self.achtelOktav = QtWidgets.QRadioButton("+- an eighth octave around band middel")
        # adding buttons to a button group to connect them logically
        # only one button is allowed to be clicked at a time
        # button index is equivelent to the corresponding denominator for the
        # exponent used to calculate the cutof frequencies
        self.group_buttons = QtWidgets.QButtonGroup()
        self.group_buttons.addButton(self.oktav, 1)
        self.group_buttons.addButton(self.halbOktav, 2)
        self.group_buttons.addButton(self.viertelOktav, 4)
        self.group_buttons.addButton(self.achtelOktav, 8)
        self.grid.addWidget(self.group_buttons.button(1), 0, 0)
        self.grid.addWidget(self.group_buttons.button(2), 1, 0)
        self.grid.addWidget(self.group_buttons.button(4), 2, 0)
        self.grid.addWidget(self.group_buttons.button(8), 3, 0)

        # LineEdit that takes the number of repeats
        self.n = QtWidgets.QLineEdit()
        self.n.setValidator(QtGui.QIntValidator(1, 50))
        self.nLabel = QtWidgets.QLabel("repetitions:")

        # Button to add an noiseband
        self.addButton = QtWidgets.QPushButton("Add noise band")
        # add the different widgets at the right place
        self.grid.addWidget(self.addButton, self.number_of_bandwidth, 0)
        self.grid.addWidget(self.n, self.number_of_bandwidth + 1, 1)
        self.grid.addWidget(self.nLabel, self.number_of_bandwidth + 1, 0)
        self.addButton.clicked.connect(self.addCycle)
        self.addCycle()
        # self.move(300, 150)
        # self.setWindowTitle('Turner')
        # self.show()
        self.setWindowTitle('GPIAS measurements')

    # updates UI, is to be called after a Cycle is added to setCycles
    # or after rejecting the dialog. This resores the values that have been
    # entered in an earlier dialog
    def updateUI(self):
        # loop over all bandmiddles
        for i, items in enumerate(self.setCycles):
            # check if deleted
            if items == None:
                continue
            # loop over all widgets needed for one bandmiddle
            for j, item in enumerate(items):
                # add the widgets at the right position
                self.grid.addWidget(item, i + self.number_of_bandwidth, j)
        # add the widgets which are at the bottom
        self.grid.addWidget(self.addButton, len(self.setCycles) + self.number_of_bandwidth, 0)
        self.grid.addWidget(self.n, len(self.setCycles) + self.number_of_bandwidth + 1, 1)
        self.grid.addWidget(self.nLabel, len(self.setCycles) + self.number_of_bandwidth + 1, 0)
        self.grid.addWidget(self.buttons, len(self.setCycles) + self.number_of_bandwidth + 2, 0, 1, 2)
        self.adjustSize()

    # this is called after the dialog was rejected while adjusting it.
    # all widgets are removed and the right ones are repainted
    def updateUiAfterAdjust(self):
        # loop over rows in grid layout
        for i in range(4, self.grid.rowCount()):
            # loop over columns in grid layout
            for j in range(self.grid.columnCount()):
                # get layout item which is to be deleted
                a = self.grid.itemAtPosition(int(i), int(j))
                if a != None:
                    # delete widget contained in the layout item
                    a.widget().setParent(None)
        # redraw the correct widgets
        self.updateUI()

    # add everything thats needed to enter one more noiseband
    def addCycle(self):
        bandMitte = QtWidgets.QLineEdit()
        # Adjust this with Bandwith and sampleFrequency
        bandMitte.setValidator(QtGui.QIntValidator(-20000, 20000))
        # button to delete this bandmiddle
        deleteButton = QtWidgets.QPushButton("delete")

        # function that delete all widgets associated with the specified bandmiddle
        def deleteRow():
            row = self.grid.getItemPosition(self.grid.indexOf(deleteButton))[0]
            print("row" + str(row))
            # loop over widgets for this bandmiddle
            for i in self.setCycles[row - self.number_of_bandwidth]:
                # delete widget
                i.setParent(None)
            # remove bandmiddle from setCycles
            self.setCycles[row - self.number_of_bandwidth] = None
            self.adjustSize()

        deleteButton.clicked.connect(deleteRow)
        # append the widgets to setCyclese
        self.setCycles.append([QtWidgets.QLabel("band middel:"),
                               bandMitte,
                               QtWidgets.QLabel("[Hz]"),
                               deleteButton])
        # redrawUI
        self.updateUI()

    # checks wether all the entries are correct and handles it appropiately
    def checkAccept(self):
        cycles = self.setCycles
        # only paramter is needed
        parameters, dummi, dummi, dummi = self.parameter()
        print(parameters)
        for items in cycles:
            if items == None:
                continue
            if not items[1].hasAcceptableInput():
                self.warning("One of the band middels is not within the allowed range")
                return
            if abs(int(items[1].text())) < 350 and int(items[1].text()) != 0:
                self.warning("One of the band middels is not within the allowed range")
                return
        if self.group_buttons.checkedId() <= 0:
            self.warning("The band width needs to be specified")
            return
        if not self.n.hasAcceptableInput():
            self.warning("repetitions is not in the allowed range")
            return
        if parameters == []:
            self.warning("Atleas one band middel needs to be specified")
            return
        # check wether two bandmiddles contain the same value
        if len(parameters) != len(set(parameters)):
            self.warning("There are two band middels with the same value")
        else:
            # if everything is entered correctly you will end here
            self.accept()

    # send a warning Message Box to the user with the message defined in str
    def warning(self, str):
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(str)
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    # returns the entered Parameters in the form
    # ([list with all band centers],n,nenner reference to setCycles)
    # [list with all band centers] => a list with itnegers which contain all bandmiddles
    # n => number of trials
    # nenner => denominator for the exponent which is used to calculate the
    # cutof frequencies of the noise
    def parameter(self):
        output = []
        # loop over bandmiddle widgets
        for a in self.setCycles:
            # if not deleted
            if a != None:
                # if a bandmiddle is entered
                if a[1].text() != "":
                    output.append(int(a[1].text()))
        try:
            # if n is entered
            return (output, int(self.n.text()), self.group_buttons.checkedId(), self.setCycles)
        except ValueError:
            # if no n is entered
            return (output, self.n.text(), self.group_buttons.checkedId(), self.setCycles)

    # handles adjusting of the parameters
    # calls the same dialog again and returns equally to getParameter() but
    # doesn't produce a new dialog
    def adjust(self):
        result = self.exec_()
        return (self, *self.parameter(), result == QtWidgets.QDialog.Accepted)

    # static method to create the dialog and return 
    # dialog => the dialog which gets the Values. This can be used to open the
    # same Dialog again
    # paramtertList => (see parameter())
    # accepted => a boolean which declares whether the dialog has been accepted
    # by pressing ok or closed by canceled or any other way
    @staticmethod
    def getParameter(parent=None):
        dialog = TurnerDialog(parent)
        result = dialog.exec_()
        return (dialog, *dialog.parameter(), result == QtWidgets.QDialog.Accepted)


# main widget which handles dialogs and saving of the konfig array
class PlaylistGenerator(QtWidgets.QWidget):
    def __init__(self, output_path):
        super().__init__()
        self.initUI()
        # list with Hearing threshold parameters
        self.SchwellParameterList = []
        # list with all the band centers
        self.TurnerParameterList = []
        # number of repeats for turner
        self.nTurner = 0
        self.nennerTurner = 0
        # store output path
        self.output_path = output_path

    def initUI(self):
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        # gridlayout to structure UI
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # Button to add hearing threshold measurement
        self.SchwellMessungButtonAdd = QtWidgets.QPushButton("Add measurements which determine hearing thresholds")
        self.SchwellMessungButtonAdd.clicked.connect(
            self.addHearingThresholdDialog)
        self.grid.addWidget(self.SchwellMessungButtonAdd, *(0, 0))
        # Button to add Turner Paradigm measurement
        self.TurnerButtonAdd = QtWidgets.QPushButton("Add GPIAS Measurements")
        self.TurnerButtonAdd.clicked.connect(self.addTurnerDialog)
        self.grid.addWidget(self.TurnerButtonAdd, *(1, 0))

        # Button which starts generating th playlist and saving it to a npy file
        self.generateButton = QtWidgets.QPushButton("Save playlist")

        # Select a file to safe. Fiel doesnt need to exist but has .npy ending
        # priot to saving at least one measurement needs to be done
        def selectFile():
            # check whether at least one measurement was added if not inform the user
            if (self.SchwellParameterList == [] and
                    self.TurnerParameterList == []):
                msg = QtWidgets.QMessageBox(parent=self)
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("Add atleast one measurement")
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg.exec_()
            else:
                # get the path to which the konfig array is supposed to be safed
                path = QtWidgets.QFileDialog.getSaveFileName(filter="byteType (*.npy)",
                                                   directory=self.output_path)
                if not path[0] == "":
                    # generate the array and get the correct file ending
                    arr, endung = self.generateKonfigArray()
                    # add ending to path
                    mypath = path[0]
                    if mypath.find(endung + ".npy") == -1:
                        idx = mypath.rfind(".npy")
                        if idx == -1:
                            raise RuntimeError
                        mypath = mypath[:idx] + endung + mypath[idx:]
                        # save file to the requested directory
                    print(5)
                    file = open(mypath, "wb")
                    np.save(file, arr, allow_pickle=False)
                    msg = QtWidgets.QMessageBox(parent=self)
                    # inform the user
                    msg.setIcon(QtWidgets.QMessageBox.Information)
                    print(6)
                    msg.setText("File has been saved to: " + mypath)
                    msg.setWindowTitle("Savingpath")
                    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msg.exec_()
                    print(7)
                    file.close()
                    self.close()

        self.generateButton.clicked.connect(selectFile)
        self.grid.addWidget(self.generateButton, *(2, 0))

        # add information about how long the requested measurement will take.
        # this will not be exactly correct as the time a measurement needs is random
        # but, taking the mean value for the time will give a good idea
        self.timeNeededApproxamitely = QtWidgets.QLineEdit("The measurements with the current setting take roundabout 0 minutes")
        self.timeNeededApproxamitely.setReadOnly(True)
        self.grid.addWidget(self.timeNeededApproxamitely, 3, 0)

        self.move(300, 150)
        self.setWindowTitle('Open GPIAS - Protocol Creator')
        self.show()

    # use BachendPlaylist to generate konfig array
    # generate an array, which is used to generate stmulation,
    # each measurement is represented in on row
    # each row looks like:
    # [noise, noiseGap,noiseFreqMin, noiseFreqMax, preStimAtten, preStimFreq, ISI, noiseTime]
    # noise           => whether a noise is played ot not
    # noiseGap        => whether a noise Gap occures(only relevant if noise is true)
    # noiseFreqMin/Max=> cutoff frequences of the noise in Hz
    # preStimAtten    => Attenuation of the prestimulus in dBspl negative values
    #                   mean no prestimulus at all
    # preStimFreq     => Frequency of the preStimulus in Hz
    #                   At this moment no band prestimulus is possible,
    #                   StimuluationBackend would need a update to do so
    # ISI             => Inter Stimulus Intervall in ms, Time between two stimuli
    #                   Randomised inbetween 6 and 14, only relevant if no noise 
    #                   is present as the noise time fullfills the job of ISI  
    # noiseTime       => Time a noise is present in ms, Randomised between 6 and 14

    # ending is the ending the konfig file is supposed to have
    # only hearingthreshold measurement => _HEARINGTHRESHOLD
    # only tinnitus perception =>_TURNER
    # both =>_TURNER_AND_HEARINGTHRESHOLD
    def generateKonfigArray(self):
        return (BackendPlaylist.generateKonfigArray(self.SchwellParameterList,
                                                    self.TurnerParameterList,
                                                    self.nTurner,
                                                    self.nennerTurner))

    # generate a Hearing threshold Dialog to get paramters from the user
    def addHearingThresholdDialog(self):
        self.DialogSchwellMessung, parameterList, ok = HearingThresholdDialog.getParameter()
        if ok:
            self.SchwellParameterList = parameterList
            self.grid.removeWidget(self.SchwellMessungButtonAdd)
            self.SchwellMessungButtonAdd.deleteLater()
            self.SchwellMessungButtonAdd = None

            self.SchwellMessungAdjust = QtWidgets.QPushButton("Change measurements which determine hearing threshold")
            self.SchwellMessungAdjust.clicked.connect(
                self.adjustHearingThresholdDialog)

            self.SchwellMessungRemove = QtWidgets.QPushButton("Delete measurements which determine hearing threshold")
            self.SchwellMessungRemove.clicked.connect(
                self.removeHearingThresholdDialog)

            self.grid.addWidget(self.SchwellMessungAdjust, 0, 0)
            self.grid.addWidget(self.SchwellMessungRemove, 0, 1)
            self.update_time_needed()

    # adjust an exisiting hearingthreshold dialog
    def adjustHearingThresholdDialog(self):
        # print(self.DialogSchwellMessung.octav.isChecked())
        self.DialogSchwellMessung, parameterList, ok = self.DialogSchwellMessung.adjust()
        if ok:
            self.SchwellParameterList = parameterList
            self.update_time_needed()
        else:
            self.DialogSchwellMessung.n.setText(str(self.SchwellParameterList[0]))
            self.DialogSchwellMessung.smallestFrequency.setText(
                str(self.SchwellParameterList[1]))
            self.DialogSchwellMessung.highestFrequency.setText(
                str(self.SchwellParameterList[2]))
            ##self.DialogSchwellMessung.frequenzFactor
            if self.SchwellParameterList[3] == 0:
                self.DialogSchwellMessung.oktav.setChecked(True)
            if self.SchwellParameterList[3] == 1:
                self.DialogSchwellMessung.halbOktav.setChecked(True)
            if self.SchwellParameterList[3] == 2:
                self.DialogSchwellMessung.viertelOktav.setChecked(True)
            self.DialogSchwellMessung.maximumPressureLevel.setText(
                str(self.SchwellParameterList[4]))
            self.DialogSchwellMessung.stepSizePressureLevel.setText(
                str(self.SchwellParameterList[5]))

    # remove existing hearing threshold measurement
    def removeHearingThresholdDialog(self):
        self.DialogSchwellMessung = None
        self.SchwellParameterList = []
        self.SchwellMessungButtonAdd = QtWidgets.QPushButton("Add measurements which determine hearing thresholds")
        self.SchwellMessungButtonAdd.clicked.connect(
            self.addHearingThresholdDialog)
        self.grid.addWidget(self.SchwellMessungButtonAdd, 0, 0)
        self.grid.removeWidget(self.SchwellMessungAdjust)
        self.grid.removeWidget(self.SchwellMessungRemove)
        self.SchwellMessungAdjust.deleteLater()
        self.SchwellMessungAdjust = None
        self.SchwellMessungRemove.deleteLater()
        self.SchwellMessungRemove = None
        self.update_time_needed()

    # generate a Turner Dialog to get Values
    def addTurnerDialog(self):
        self.DialogTurner, parameterList, n, nenner, self.setCyclesHelper, ok = TurnerDialog.getParameter()

        if ok:
            self.TurnerParameterList = parameterList
            self.nTurner = n
            self.nennerTurner = nenner

            self.grid.removeWidget(self.TurnerButtonAdd)
            self.TurnerButtonAdd.deleteLater()
            self.TurnerButtonAdd = None

            self.TurnerAdjust = QtWidgets.QPushButton("Change GPIAS Measurements")
            self.TurnerAdjust.clicked.connect(self.adjustTurnerDialog)

            self.TurnerRemove = QtWidgets.QPushButton("Delete GPIAS Measurements")
            self.TurnerRemove.clicked.connect(self.removeTurnerDialog)

            self.grid.addWidget(self.TurnerAdjust, 1, 0)
            self.grid.addWidget(self.TurnerRemove, 1, 1)
            self.update_time_needed()

    # adjust an exisiting Turner dialog
    def adjustTurnerDialog(self):
        # print(self.DialogSchwellMessung.octav.isChecked())
        oldSetCyclesHelper = copy.copy(self.setCyclesHelper)
        oldn = self.nTurner
        oldNenner = self.nennerTurner
        self.DialogTurner, parameterList, self.nTurner, self.nennerTurner, self.setCyclesHelper, ok = self.DialogTurner.adjust()
        print(oldSetCyclesHelper == self.setCyclesHelper)
        if ok:
            self.TurnerParameterList = parameterList
            self.update_time_needed()
        else:
            self.DialogTurner.setCycles = oldSetCyclesHelper
            self.setCyclesHelper = oldSetCyclesHelper
            print(self.DialogTurner.n)
            self.DialogTurner.n.setText(str(oldn))
            self.nTurner = oldn

            self.nennerTurner = oldNenner
            self.DialogTurner.group_buttons.button(oldNenner).setChecked(True)
            self.DialogTurner.updateUiAfterAdjust()

    # remove existing Turner measurement
    def removeTurnerDialog(self):
        self.DialogTurner = None
        self.TurnerParameterList = []
        self.nTurner = 0
        self.nennerTurner = 0
        self.TurnerButtonAdd = QtWidgets.QPushButton("Add GPIAS Measurements")
        self.TurnerButtonAdd.clicked.connect(self.addTurnerDialog)
        self.grid.addWidget(self.TurnerButtonAdd, 1, 0)
        self.grid.removeWidget(self.TurnerAdjust)
        self.grid.removeWidget(self.TurnerRemove)
        self.TurnerAdjust.deleteLater()
        self.TurnerAdjust = None
        self.TurnerRemove.deleteLater()
        self.TurnerRemove = None
        self.update_time_needed()

    def update_time_needed(self):
        if self.TurnerParameterList != []:
            timeTurner = self.nTurner * 11 * len(self.TurnerParameterList) * 2
        else:
            timeTurner = 0

        if self.SchwellParameterList != []:
            if self.SchwellParameterList[3] == 2:
                adjustfactor = 4
            else:
                adjustfactor = self.SchwellParameterList[3] + 1
            ##n * 11 *(1+maximaleLautstärke/schrittgrößeLautstärke)*(1+log2(größtefrequenz/kleisntefrequenz)*adjustFactor)
            timeSchwelle = (self.SchwellParameterList[0] * 11 *
                            (1 + self.SchwellParameterList[4] / self.SchwellParameterList[5]) *
                            (1 + np.log2(self.SchwellParameterList[2] / self.SchwellParameterList[1]) * adjustfactor))
        else:
            timeSchwelle = 0
        self.timeNeededApproxamitely.setText("The measurements with the current setting take roundabout " + str(
            int((timeSchwelle + timeTurner) / 60) + 1) + " minutes")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = PlaylistGenerator("")
    app.exec_()
