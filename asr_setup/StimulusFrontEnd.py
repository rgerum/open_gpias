# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 12:56:07 2017

@author: rahlfshh
"""

import os
import sys
import time
import numpy as np
from qtpy import QtCore, QtGui, QtWidgets
import qtawesome as qta
from threading import Thread
from . import StimulusBackend
from . import Plot_Klasse
from . import gui_helpers
from .MeasurementPlot import plotWidget


# add exception hook hack to prevent from python just crashing without throwing an exception, which occurs on some Qt5 installations
def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = my_excepthook


Playlist_Directory = "D:/Users/Setup/Desktop/Playlists"
Measurement_Directory = "D:/Users/Setup/Desktop/Messungen"
Backup_Measurement_Directory = "D:/Users/Setup/Backup_messungen"


class measurementGui(QtWidgets.QWidget):
    timeString = ""
    shutDown = 0
    thisplot = None
    backup_plot_count = 0

    measurement_thread = None
    plot_window = None

    def __init__(self, parent, protocol, config):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Measure")
        self.parent = parent
        self.parent.settingsUpdated.connect(self.statusUpdated)

        self.dir_measurements = Measurement_Directory

        layout1 = QtWidgets.QVBoxLayout(self)

        layout2 = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout2)

        layout_properties = QtWidgets.QVBoxLayout()
        layout2.addLayout(layout_properties)
        self.textEdit_Experimenter = gui_helpers.addLineEdit(layout_properties, "Experimenter:", "Experimenter")
        self.textEdit_Mousname = gui_helpers.addLineEdit(layout_properties, "Animal name:", "Mouse")
        self.textEdit_status = gui_helpers.addLineEdit(layout_properties, "Animal status:", "pre or post")

        self.textEdit_Experimenter.textEdited.connect(self.statusUpdated)
        self.textEdit_Mousname.textEdited.connect(self.statusUpdated)
        self.textEdit_status.textEdited.connect(self.statusUpdated)

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

        self.plot = plotWidget()
        layout1.addWidget(self.plot)

        layout_buttons = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout_buttons)

        self.startButton = gui_helpers.addPushButton(layout_buttons, "Start Measurement", self.startStimulation, icon=qta.icon("fa.play"))
        self.pauseButton = gui_helpers.addPushButton(layout_buttons, "Pause Measurement", self.pause, icon=qta.icon("fa.pause"))
        self.stopButton = gui_helpers.addPushButton(layout_buttons, "Stop Measurement", self.stop, icon=qta.icon("fa.stop"))

        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)

        self.measurement_thread = StimulusBackend.Measurement(protocol, config)
        self.measurement_thread.plot_data.connect(self.plot_it)
        self.measurement_thread.backup.connect(self.save_backup)
        self.measurement_thread.finished.connect(self.m_finished)
        self.measurement_thread.paused.connect(self.m_paused)
        self.measurement_thread.stopped.connect(self.m_stopped)
        self.measurement_thread.resumed.connect(self.m_resumed)
        self.measurement_thread.update_timer.connect(self.update_timer)

        self.statusUpdated()

        self.textEdit_out.addLog("Program started")

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
        self.pauseButton.setEnabled(False)
        self.startButton.setEnabled(False)

        if self.measurement_thread is not None:
            #self.textEdit_out.setText('Stopping Measurement. Please wait') # TODO
            self.measurement_thread.stop = True
            self.measurement_thread.pause = False  # In case it was previously paused
        # self.timer.stop()

    def pause(self):  # pause button pushed
        """
        Callback function for pause button
        """
        if self.measurement_thread is not None:
            if self.measurement_thread.pause:
                self.pauseButton.setText("Pause")
                self.measurement_thread.pause = False
            else:
                self.pauseButton.setText("Resume")
                self.pauseButton.setEnabled(False)
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
        if self.measurement_thread is not None and self.measurement_thread.pause:
            self.measurement_thread.pause = False
            return

        # reset this to notify save_data
        self.timeString = ""

        #self.textEdit_out.clear()  # clears output text
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.pauseButton.setEnabled(True)

        self.pauseButton.setText("Pause")

        self.textEdit_out.addLog("Measurement started")

        Thread(target=self.measurement_thread.run_thread, args=()).start()  # start Measurement
        time.sleep(1)

    def update_timer(self, konfigArray, idx):
        self.progressBar.setRange(0, len(konfigArray))
        self.progressBar.setValue(idx+1)
        if idx >= 0:
            digits = len(str(len(konfigArray)))
            self.textEdit_out.addLog(("Trial %"+str(digits)+"d/%d finished.") % (idx+1, len(konfigArray)))
        min_left = self.calculate_time_left(konfigArray, idx)
        self.labelRemaining.setText("Remaining time: %d min" % min_left)

    def calculate_time_left(self, konfigArray, idx):
        noisetimes = konfigArray[idx:, StimulusBackend.noiseTimeIDX]
        ISIs = konfigArray[idx:, StimulusBackend.ISIIDX]
        msleft = np.sum(ISIs) + np.sum(noisetimes) + 2000 * len(ISIs)
        return int(msleft / (1000 * 60)) + 1

    def save_backup(self, data_extracted, all_data):
        if self.backup_plot_count >= 10:
            self.save_data(data_extracted, all_data, finished=False)
            self.backup_plot_count = 0
        else:
            self.backup_plot_count += 1

    def plot_it(self, data, idx):
        # provide teh plot with the data
        self.plot.setData(data[idx, :, :], idx)
        data[idx][6][0] = self.plot.get_max()

    def m_finished(self, data_extracted, all_data):
        self.save_data(data_extracted, all_data)
        self.textEdit_out.addLog("Measurement finished")
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.measurement_thread = None
        self.measurement_thread = None
        QtWidgets.QMessageBox.information(self, 'Finished', 'Measurement Completed')

    def m_paused(self):
        # self.timer.stop()
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.textEdit_out.addLog("Measurement paused")
        QtWidgets.QMessageBox.information(self, 'Paused', 'The door can be opened.')

    def m_resumed(self):
        self.pauseButton.setEnabled(True)
        self.textEdit_out.setText('')

    def m_stopped(self):
        self.textEdit_out.addLog("Measurement stopped")
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        if self.measurement_thread is not None:
            self.measurement_thread.pause = False  # reset in case pause button was pressed
        QtWidgets.QMessageBox.information(self, 'Stopped', 'Measurement stopped.')
        self.measurement_thread = None
        if self.shutDown:
            self.shutDown = 2
            self.close()

    def save_data(self, data_extracted, all_data, finished=True):

        if self.timeString == "":
            self.timeString = time.strftime("%Y-%m-%d_%H-%M")

        if self.turner and self.hearingThreshold:
            fileNameEnding = "_turner_and_threshold"
        elif self.turner:
            fileNameEnding = "_turner"
        elif self.hearingThreshold:
            fileNameEnding = "_threshold"
        else:
            raise RuntimeError
        dirname = os.path.join(self.textEdit_Experimenter.text(), self.textEdit_Mousname.text(),
                               self.textEdit_status.text(), self.timeString)
        filename = "UNFINISHED_" + self.textEdit_Experimenter.text() + '_' + self.textEdit_Mousname.text() + '_' + self.textEdit_status.text() + "_" + fileNameEnding + "_" + self.timeString
        directory = os.path.join(self.dir_measurements, dirname)

        if not os.path.exists(directory):
            os.makedirs(directory)

        np.save(os.path.join(directory, filename + '_extracted_data.npy'), data_extracted)

        if finished:
            time.sleep(3)
            # print(data_extracted[0])
            # os.rename(os.path.join(directory, filename + '_raw_data.npy'), os.path.join(directory, filename.replace("UNFINISHED_","") + '_raw_data.npy'))
            os.rename(os.path.join(directory, filename + '_extracted_data.npy'),
                      os.path.join(directory, filename.replace("UNFINISHED_", "") + '_extracted_data.npy'))
            self.timeString = ""
            only_amplitudes = self.raw_to_amplitude(data_extracted)
            np.save(os.path.join(directory, filename.replace("UNFINISHED_", "") + '_amplitudes.npy'), only_amplitudes)
            directory_backup = directory.replace(Measurement_Directory, Backup_Measurement_Directory)
            if not os.path.exists(directory_backup):
                os.makedirs(directory_backup)

            np.save(os.path.join(directory_backup, filename.replace("UNFINISHED_", "") + '_extracted_data.npy'),
                    data_extracted)

    def raw_to_amplitude(self, extracted_data):
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

        if self.measurement_thread is not None:
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


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = measurementGui()
    ex.show()
    app.exec_()


def test():
    app = QtWidgets.QApplication(sys.argv)
    ex = measurementGui()
    ex.textEdit_Experimenter.setText("Achim")
    ex.textEdit_Mousname.setText("TestMouse")
    ex.lineEdit_Path.setText(r"GUI Playlist/ein test_HEARINGTHRESHOLD.npy")
    ex.textEdit_status.setText("pre10")
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
