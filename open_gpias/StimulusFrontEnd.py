#!/usr/bin/env python
# -*- coding: utf-8 -*-
# StimulusFrontEnd.py

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

import os
import sys
import time
import numpy as np
from qtpy import QtCore, QtGui, QtWidgets
import qtawesome as qta
from threading import Thread
from . import StimulusBackend
from . import gui_helpers
from .MeasurementPlot import plotWidget


class measurementGui(QtWidgets.QWidget):
    timeString = ""
    shutDown = 0
    thisplot = None
    backup_plot_count = 0

    measurement_thread = None
    plot_window = None

    def __init__(self, parent, protocol, config, signal):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Measure")
        self.parent = parent
        self.config = config
        self.parent.settingsUpdated.connect(self.statusUpdated)

        layout1 = QtWidgets.QVBoxLayout(self)

        layout2 = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout2)

        # Metadata
        layout_properties = QtWidgets.QVBoxLayout()
        layout2.addLayout(layout_properties)
        # experimenter
        self.textEdit_Experimenter = gui_helpers.addLineEdit(layout_properties, "Experimenter:", "Experimenter")
        self.textEdit_Experimenter.textEdited.connect(self.statusUpdated)
        # animal name
        self.textEdit_Mousname = gui_helpers.addLineEdit(layout_properties, "Animal name:", "Mouse")
        self.textEdit_Mousname.textEdited.connect(self.statusUpdated)
        # animal status
        self.textEdit_status = gui_helpers.addLineEdit(layout_properties, "Animal status:", "pre or post")
        self.textEdit_status.textEdited.connect(self.statusUpdated)

        # status display
        self.status_bar = gui_helpers.QStatusBar(dict(Soundcard=False, NiDAQ=False, Protocol=False, Metadata=False), layout_properties)
        layout_properties.addStretch()

        layout_properties2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(layout_properties2)

        # Label
        self.labelStatus = QtWidgets.QLabel("Measurement status:")
        layout_properties2.addWidget(self.labelStatus)

        # Progress Bar
        self.progressBar = QtWidgets.QProgressBar()
        layout_properties2.addWidget(self.progressBar)
        self.progressBar.setFormat("%v/%m")

        # Remaining time
        self.labelRemaining = QtWidgets.QLabel("Remaining time:")
        layout_properties2.addWidget(self.labelRemaining)

        self.textEdit_out = gui_helpers.addLogBox(layout_properties2, "Output:")
        layout_properties2.addStretch()

        self.plot = plotWidget(config=config)
        layout1.addWidget(self.plot)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout_buttons)

        # measurement control buttons
        self.startButton = gui_helpers.addPushButton(layout_buttons, "Start Measurement", self.startStimulation, icon=qta.icon("fa.play"))
        self.pauseButton = gui_helpers.addPushButton(layout_buttons, "Pause Measurement", self.pause, icon=qta.icon("fa.pause"))
        self.stopButton = gui_helpers.addPushButton(layout_buttons, "Stop Measurement", self.stop, icon=qta.icon("fa.stop"))

        self.setButtonStatus(0)

        self.measurement_thread = StimulusBackend.Measurement(protocol, config, signal)
        self.measurement_thread.trial_finished.connect(self.trialFinishedEvent)
        self.measurement_thread.measurement_finished.connect(self.m_finished)
        self.measurement_thread.paused.connect(self.m_paused)
        self.measurement_thread.stopped.connect(self.m_stopped)
        self.measurement_thread.resumed.connect(self.m_resumed)
        self.parent.settingsUpdated.connect(self.measurement_thread.signal.loadConfig)

        self.measurement_thread.error.connect(self.textEdit_out.addLog)

        self.statusUpdated()

        self.textEdit_out.addLog("Program started")

        if 0:
            data = np.load(r"D:\Repositories\open_gpias\open_gpias\Achim_LS01_pre__turner_and_threshold_2018.npy")

            self.plt_index = 10
            self.plot_it(data, self.plt_index)

            layout_navigate = QtWidgets.QHBoxLayout(self)
            layout_properties.addLayout(layout_navigate)
            gui_helpers.addPushButton(layout_navigate, "", self.navigateLeft, icon=qta.icon("fa.arrow-left"))
            self.label_title = QtWidgets.QSpinBox()
            self.label_title.setSuffix(" / 0")
            self.label_title.setPrefix("Trial ")
            self.label_title.setRange(0, 400)
            self.label_title.setAlignment(QtCore.Qt.AlignCenter)
            self.label_title.valueChanged.connect(self.plotOutputSignal)
            layout_navigate.addWidget(self.label_title)
            gui_helpers.addPushButton(layout_navigate, "", self.navigateRight, icon=qta.icon("fa.arrow-right"))

    def navigateLeft(self):
        self.plt_index -= 1
        self.label_title.setValue(self.plt_index)

    def plotOutputSignal(self):
        data = np.load(r"D:\Repositories\open_gpias\open_gpias\Achim_LS01_pre__turner_and_threshold_2018.npy")
        self.plot_it(data, self.plt_index)

    def navigateRight(self):
        self.plt_index += 1
        self.label_title.setValue(self.plt_index)

    def trialFinishedEvent(self, data_extracted, idxStartle, protocol):
        self.plot_it(data_extracted, idxStartle)
        self.save_backup(data_extracted)
        self.update_timer(protocol, idxStartle)

    def setButtonStatus(self, status):
        if status == 0:  # no measurement
            self.startButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.stopButton.setEnabled(False)
        if status == 1:  # running measurement
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.stopButton.setEnabled(True)
        if status == 2:  # pause measurement
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.stopButton.setEnabled(False)
        if status == -1:  # waiting to stop or pause
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(False)
            self.stopButton.setEnabled(False)

    def statusUpdated(self):
        status = dict(Soundcard=self.measurement_thread.signal.checkSettings(),
                      NiDAQ=self.measurement_thread.checkNiDAQ(),
                      Protocol=self.measurement_thread.protocolWidget.checkProtocol(),
                      Metadata=self.checkData())
        self.status_bar.setStatus(status)

    def stop(self):  # stop button pushed
        """
        Callback function for stop button, stops and resets measurement
        """
        self.setButtonStatus(-1)

        #self.textEdit_out.setText('Stopping Measurement. Please wait') # TODO
        self.measurement_thread.stop = True
        self.measurement_thread.pause = False  # In case it was previously paused
        # self.timer.stop()

    def pause(self):  # pause button pushed
        """
        Callback function for pause button
        """
        if self.measurement_thread.pause:
            self.pauseButton.setText("Pause")
            self.measurement_thread.pause = False
            self.setButtonStatus(-1)
        else:
            self.pauseButton.setText("Resume")
            self.setButtonStatus(-1)
            #self.textEdit_out.setText('Pausing Measurement. Please wait') # TODO
            self.measurement_thread.pause = True

    def startStimulation(self):
        """
        Start the stimulation and recording.
        """
        # Check the input fields
        ok1, message1 = self.checkData()
        ok2, message2 = self.measurement_thread.protocolWidget.checkProtocol()
        ok3, message3 = self.measurement_thread.signal.checkSettings()
        message = ""
        if not ok1:
            message += message1+"\n"
        if not ok2:
            message += message2+"\n"
        if not ok3:
            message += message3+"\n"
        if not ok1 or not ok2 or not ok3:
            QtWidgets.QMessageBox.critical(self, 'Error', message)
            return

        # If the measurement is paused, resume it
        if self.measurement_thread.pause:
            self.measurement_thread.pause = False
            return
        self.measurement_thread.stop = False

        # reset this to notify save_data
        self.timeString = ""

        self.setButtonStatus(1)

        self.pauseButton.setText("Pause")

        self.textEdit_out.addLog("Measurement started")

        Thread(target=self.measurement_thread.run_thread, args=()).start()  # start Measurement

    def update_timer(self, protocol, idx):
        self.progressBar.setRange(0, len(protocol))
        self.progressBar.setValue(idx+1)
        if idx >= 0:
            digits = len(str(len(protocol)))
            self.textEdit_out.addLog(("Trial %"+str(digits)+"d/%d finished.") % (idx+1, len(protocol)))
        # print the remaini
        self.labelRemaining.setText("Remaining time: %s" % str(self.measurement_thread.signal.getProtocolDuration(protocol, idx)).split(".")[0])

    def save_backup(self, data_extracted):
        self.save_data(data_extracted, finished=False)
        return
        if self.backup_plot_count >= 10:
            self.save_data(data_extracted, finished=False)
            self.backup_plot_count = 0
        else:
            self.backup_plot_count += 1

    def plot_it(self, data, idx):
        """ provide the plot with the data """
        print("plot_id", data.shape, idx)
        self.plot.setData(data[idx, :, :], idx)
        data[idx][6][0] = self.plot.get_max()

    def m_finished(self, data_extracted, empty):
        self.save_data(data_extracted, finished=True)
        self.textEdit_out.addLog("Measurement finished")
        self.setButtonStatus(0)
        QtWidgets.QMessageBox.information(self, 'Finished', 'Measurement Completed')

    def m_paused(self):
        # self.timer.stop()
        self.setButtonStatus(2)
        self.textEdit_out.addLog("Measurement paused")
        QtWidgets.QMessageBox.information(self, 'Paused', 'The door can be opened.')

    def m_resumed(self):
        self.setButtonStatus(1)
        self.textEdit_out.addLog("Measurement resumed")

    def m_stopped(self):
        self.textEdit_out.addLog("Measurement stopped")
        self.setButtonStatus(0)
        self.measurement_thread.pause = False  # reset in case pause button was pressed
        QtWidgets.QMessageBox.information(self, 'Stopped', 'Measurement stopped.')
        if self.shutDown:
            self.shutDown = 2
            self.close()

    def save_data(self, data_extracted, finished=True):

        # add time from first trial
        if self.timeString == "":
            self.timeString = time.strftime("%Y-%m-%d_%H-%M")

        # get the string from the protocol
        fileNameEnding = self.measurement_thread.protocolWidget.getProtocolName()

        # get the string from the metadata
        metadata = [self.textEdit_Experimenter.text(), self.textEdit_Mousname.text(),
                               self.textEdit_status.text(), self.timeString]

        # join the directory tree
        dirname = os.path.join(*metadata)

        # join the data into the filename
        filename = "UNFINISHED_" + "_".join(metadata)

        # get the output directories
        directory = os.path.join(self.config.output_directory, self.config.directory_measurements, dirname)
        directory_backup = os.path.join(self.config.output_directory, self.config.directory_backup, dirname)

        # create directory
        if not os.path.exists(directory):
            os.makedirs(directory)

        # save the data to the backup folder
        np.save(os.path.join(directory, filename + '_extracted_data.npy'), data_extracted)

        # if the measurement is finished
        if finished:
            # wait?  TODO Why?
            time.sleep(3)

            # rename the file to remove the "UNFINISHED_" tag
            os.rename(os.path.join(directory, filename + '_extracted_data.npy'),
                      os.path.join(directory, filename.replace("UNFINISHED_", "") + '_extracted_data.npy'))

            # reset the time string
            self.timeString = ""

            # extract and save the amplitudes
            only_amplitudes = self.raw_to_amplitude(data_extracted)
            np.save(os.path.join(directory, filename.replace("UNFINISHED_", "") + '_amplitudes.npy'), only_amplitudes)

            # create the directory for the backup
            if not os.path.exists(directory_backup):
                os.makedirs(directory_backup)

            # save the data to the backup folder
            np.save(os.path.join(directory_backup, filename.replace("UNFINISHED_", "") + '_extracted_data.npy'),
                    data_extracted)

    def movementCheck(self, data):
        """ check if animal has moved before noise burst """
        # data until threshold
        val = data[:8000]
        if max(val) > self.config.acceleration_threshold:
            return False
        else:
            return True

    def get_max(self, data):
        """
        Calculation of max acceleration
        """
        # calculation of maximum only if trial is valid
        if self.movementCheck(data):
            # searching for maximum after stimulus
            return max(data[800:])
        else:
            return np.NaN

    def rms(self, data_x, data_y, data_z):
        """ calculation of root mean square data and low pass filtering """
        data = np.empty(shape=(data_x.__len__(), 1))

        data_xf = self.butter_lowpass_filter(data_x)
        data_yf = self.butter_lowpass_filter(data_y)
        data_zf = self.butter_lowpass_filter(data_z)

        sensitivity = self.config.acceleration_sensor_sensitivity_v_to_g
        data = np.sqrt((data_xf / sensitivity) ** 2 + (data_yf / sensitivity) ** 2 + (data_zf / sensitivity) ** 2)
        return data

    def raw_to_amplitude(self, extracted_data):
        # HINT: 6 is the index of the headerline

        # extract the maximal amplitude of each trial
        for idx in range(len(extracted_data)):
            # get the filtered rms of x, y, z
            data = self.rms(extracted_data[idx][0], extracted_data[idx][1], extracted_data[idx][2])
            extracted_data[idx][6][0] = self.get_max(data)

        only_amplitude = np.zeros((len(extracted_data), 10))
        for i, item in enumerate(extracted_data):
            only_amplitude[i] = item[6][:10]
        #        local_amplitudeIDX = 0
        #        local_noiseIDX = 1
        #        local_noiseGapIDX = 2
        local_noiseFreqMinIDX = 3
        local_noiseFreqMaxIDX = 4
        local_preStimAttenIDX = 5
        #        local_preStimFreqIDX = 6
        #        local_ISIIDX = 7
        #        local_noiseTimeIDX = 8
        local_noiseFreqMidIDX = 9
        noise_atten = 60
        for i in range(len(only_amplitude)):
            if only_amplitude[i][local_noiseFreqMinIDX] != 0:
                only_amplitude[i][local_noiseFreqMidIDX] = int(only_amplitude[i][local_noiseFreqMinIDX] * (
                            only_amplitude[i][local_noiseFreqMaxIDX] / only_amplitude[i][local_noiseFreqMinIDX]) ** (
                                                                           1 / 2) + 1)
                only_amplitude[i][local_preStimAttenIDX] = noise_atten
        return only_amplitude

    def closeEvent(self, event):
        """
        our own close event to prevent the user from closing without intention
        further more the measurement thread is closed
        """
        if self.shutDown == 1:
            event.ignore()
            return
        if self.shutDown == 2:
            if self.thisplot:
                self.thisplot.esc()  # MS
            return

        if self.measurement_thread is not None:  # TODO check running
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "warning",
                              "Sind sie sich sicher, dass Sie die Messung schließen" +
                              " möchten? Es ist nicht möglich die Messung zu einem" +
                              " späteren Zeitpunkt fortzuführen!")
            msg.addButton(QtWidgets.QMessageBox.Ok)
            msg.addButton(QtWidgets.QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QtWidgets.QMessageBox.Ok:

                self.textEdit_out.setText('Stopping Measurement. Please wait')
                self.measurement_thread.stop = True
                self.measurement_thread.pause = False
                self.shutDown = 1
                event.ignore()
            else:
                event.ignore()
        else:
            if self.thisplot:
                self.thisplot.esc()  # MS

    def checkData(self):
        """
        Checks the entries of the textEdit Fields
        and shows Error Message if it is not correct"

        Returns
        -------
            False: Exception/Error while reading testEdit Field
            True: Entries correct
        """
        errors = []

        # check if mouse name is given
        if self.textEdit_Mousname.text() == "":
            errors.append("Please fill in mouse name")

        # check if experimenter name is given
        if self.textEdit_Experimenter.text() == '':
            errors.append("Please fill in experimenter name")

        # check if status is given
        status = self.textEdit_status.text().strip()
        if status == "":
            errors.append("Please fill in status")
        else:
            # check if status is either pre or post followed by an integer
            allowed_status_texts = ["pre", "post"]
            for text in allowed_status_texts:
                if status.startswith(text):
                    value = status[len(text):].strip()
                    status = text
            # try to set the text (removing possible spaces in the status)
            try:
                if status == "post":
                    self.textEdit_status.setText("%s%d" % (status, int(value)))
                elif status == "pre":
                    self.textEdit_status.setText("%s" % (status))
                else:
                    raise ValueError
            except (ValueError, UnboundLocalError):
                errors.append("Status has to be either 'pre' or 'post' followed by an integer.")

        # do we have errors? warn the user!
        if len(errors):
            return False, "\n".join(errors)
        # if not, everything is fine
        return True, "Mouse %s measured by %s in state %s" % (self.textEdit_Mousname.text(), self.textEdit_Experimenter.text(), self.textEdit_status.text())


    ##########low pass filter##########
    def butter_lowpass(self, cutoff, oder, sf):
        from scipy.signal import butter
        N = oder
        Fc = cutoff
        nyq = sf / 2
        b, a = butter(N, Fc / nyq, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(self, data):
        from scipy.signal import lfilter
        b, a = self.butter_lowpass(45, 6, 10000)
        y = lfilter(b, a, data)
        return y
    ###################################