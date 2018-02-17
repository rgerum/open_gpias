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
from threading import Thread
from . import StimulusBackend
from . import Plot_Klasse


# add exception hook hack to prevent from python just crashing without throwing an exception, which occurs on some Qt5 installations
def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = my_excepthook


Playlist_Directory = "C:/Users/Setup/Desktop/Playlists"
Measurement_Directory = "C:/Users/Setup/Desktop/Messungen"
Backup_Measurement_Directory = "C:/Users/Setup/Backup_messungen"


class QFileChooseEdit(QtWidgets.QWidget):
    def __init__(self, directory, filter):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setReadOnly(True)
        self.layout.addWidget(self.lineEdit)

        self.buttonBrowser = QtWidgets.QPushButton("Open...")
        self.buttonBrowser.clicked.connect(self.selectFile)
        self.layout.addWidget(self.buttonBrowser)

        self.directory = directory
        self.filter = filter

    def selectFile(self):
        self.lineEdit.setText(QtWidgets.QFileDialog.getOpenFileName(directory=self.directory, filter=self.filter)[0])

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)


class LoadAndPlayKonfig(QtWidgets.QWidget):
    timeString = ""
    shutDown = 0
    thisplot = None
    backup_plot_count = 0

    measurement_thread = None
    plot_window = None

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Measure")

        self.dir_measurements = Measurement_Directory

        layout1 = QtWidgets.QVBoxLayout(self)

        layout2 = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout2)

        layout_properties = QtWidgets.QVBoxLayout()
        layout2.addLayout(layout_properties)
        self.textEdit_Experimenter = self.addLineEdit(layout_properties, "Experimenter:", "Experimenter")
        self.textEdit_Mousname = self.addLineEdit(layout_properties, "Animal Name:", "Mouse")
        self.lineEdit_Path = self.addFileChooser(layout_properties, "Protocol File:")
        self.lcdNumber = self.addLCDNumber(layout_properties, "Measurement Duration:")
        layout_properties.addStretch()

        layout_properties2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(layout_properties2)
        self.textEdit_status = self.addLineEdit(layout_properties2, "Status:", "pre or post")
        self.textEdit_out = self.addTextBox(layout_properties2, "Output:")
        layout_properties2.addStretch()

        layout_buttons = QtWidgets.QHBoxLayout()
        layout1.addLayout(layout_buttons)

        self.startButton = self.addPushButton(layout_buttons, "Start Measurement", self.startStimulation)
        self.pauseButton = self.addPushButton(layout_buttons, "Pause Measurement", self.pause)
        self.stopButton = self.addPushButton(layout_buttons, "Stop Measurement", self.stop)

        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)

    def addPushButton(self, layout, name, function):
        button = QtWidgets.QPushButton(name)
        button.clicked.connect(function)
        layout.addWidget(button)
        return button

    def addLabel(self, layout, name):
        label = QtWidgets.QLabel(name)
        layout.addWidget(label)

    def addLineEdit(self, layout, name, placeholder):
        self.addLabel(layout, name)

        edit = QtWidgets.QLineEdit()
        edit.setPlaceholderText(placeholder)
        layout.addWidget(edit)
        return edit

    def addTextBox(self, layout, name):
        self.addLabel(layout, name)

        edit = QtWidgets.QTextEdit()
        layout.addWidget(edit)
        return edit

    def addFileChooser(self, layout, name):
        self.addLabel(layout, name)

        edit = QFileChooseEdit(Playlist_Directory, "byteType (*_HEARINGTHRESHOLD.npy *_TURNER.npy *_TURNER_AND_HEARINGTHRESHOLD.npy)")
        layout.addWidget(edit)
        return edit

    def addLCDNumber(self, layout, name):
        self.addLabel(layout, name)

        edit = QtWidgets.QLCDNumber()
        edit.display(0)
        layout.addWidget(edit)
        return edit

    def stop(self):  # stop button pushed
        """
        Callback function for stop button, stops and resets mesurement
        """
        self.pauseButton.setEnabled(False)
        self.startButton.setEnabled(False)

        if self.measurement_thread is not None:
            self.textEdit_out.setText('Stopping Measurement. Please wait')
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
                self.textEdit_out.setText('Pausing Measurement. Please wait')
                self.measurement_thread.pause = True

    def startStimulation(self):
        # Check the input fields
        if not self.check_input():
            return

        # If the measurement is paused, resume it
        if self.measurement_thread is not None and self.measurement_thread.pause:
            self.measurement_thread.pause = False
            return

        # reset this to notify save_data
        self.timeString = ""

        # try to load the config file
        try:
            konfigFile = open(self.lineEdit_Path.text(), "rb")
        except IOError:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'The specified config file cannot be loaded.')
            return

        # check the content of the config file
        konfig = np.load(konfigFile, allow_pickle=False, fix_imports=False)
        if self.lineEdit_Path.text()[-11:] == "_TURNER.npy":
            self.turner = True
            self.hearingThreshold = False

            for a in konfig[5:]:
                if a[4] != 0 or a[5] != 0 or a[6] != 0 or len(a) != 8:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        elif self.lineEdit_Path.text()[-32:] == "_TURNER_AND_HEARINGTHRESHOLD.npy":
            self.turner = True
            self.hearingThreshold = True
            for a in konfig:
                if len(a) != 8:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        elif self.lineEdit_Path.text()[-21:] == "_HEARINGTHRESHOLD.npy":
            self.turner = False
            self.hearingThreshold = True
            for a in konfig:
                if a[0] != 0 or a[1] != 0 or a[2] != 0 or a[3] != 0:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        else:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'The name of the config file does not match.')
            raise RuntimeError

        # StimulusBackend.startStimulation(konfig)
        self.textEdit_out.clear()  # clears output text
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.pauseButton.setEnabled(True)

        self.pauseButton.setText("Pause")

        self.measurement_thread = StimulusBackend.Measurement(konfig, 10000)
        self.measurement_thread.plot_data.connect(self.plot_it)
        self.measurement_thread.backup.connect(self.save_backup)
        self.measurement_thread.finished.connect(self.m_finished)
        self.measurement_thread.paused.connect(self.m_paused)
        self.measurement_thread.stopped.connect(self.m_stopped)
        self.measurement_thread.resumed.connect(self.m_resumed)
        self.measurement_thread.update_timer.connect(self.update_timer)

        Thread(target=self.measurement_thread.run_thread, args=()).start()  # start Measurement
        time.sleep(1)

    def update_timer(self, konfigArray, idx):
        print("hallo1")
        min_left = self.calculate_time_left(konfigArray, idx)
        print(2)
        self.lcdNumber.display(min_left)
        print(3)

    def calculate_time_left(self, konfigArray, idx):
        print("hallo3")
        print(StimulusBackend.noiseTimeIDX)
        print(konfigArray)
        print(idx)
        noisetimes = konfigArray[idx:, StimulusBackend.noiseTimeIDX]
        ISIs = konfigArray[idx:, StimulusBackend.ISIIDX]
        print("hallo4")
        msleft = np.sum(ISIs) + np.sum(noisetimes) + 2000 * len(ISIs)
        print("hallo5")
        return int(msleft / (1000 * 60)) + 1

    def save_backup(self, data_extracted, all_data):
        if self.backup_plot_count >= 10:
            self.save_data(data_extracted, all_data, finished=False)
            self.backup_plot_count = 0
        else:
            self.backup_plot_count += 1

    # TODO MS
    def plot_it(self, data, idx):
        if self.thisplot is None:
            self.thisplot = Plot_Klasse.plotWidget(data[idx, :, :], idx)
            # saves maximum of acceleration calculated by plot
            self.thisplot.plot()
            data[idx][6][0] = self.thisplot.get_max()
        # from Plot_Klasse import plot

        else:
            # data = np.copy(data)
            self.thisplot.esc()
            # self.thisplot.deleteLater()

            self.thisplot = Plot_Klasse.plotWidget(data[idx, :, :], idx)
            # saves maximum of acceleration calculated by plot
            self.thisplot.plot()
            data[idx][6][0] = self.thisplot.get_max()

        self.thisplot.show()

    def m_finished(self, data_extracted, all_data):
        self.save_data(data_extracted, all_data)
        self.textEdit_out.setText('Measurement ended')
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        QtWidgets.QMessageBox.information(self, 'Finished', 'Measurement Completed')
        self.measurement_thread = None
        self.lcdNumber.display(0)
        self.measurement_thread = None

    def m_paused(self):
        # self.timer.stop()
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        QtWidgets.QMessageBox.information(self, 'Paused', 'The door can be opened.')
        self.textEdit_out.setText('Measurement paused')

    def m_resumed(self):
        self.pauseButton.setEnabled(True)
        self.textEdit_out.setText('')

    def m_stopped(self):
        self.textEdit_out.setText('Measurement stopped')
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        if self.measurement_thread is not None:
            self.measurement_thread.pause = False  # reset in case pause button was pressed
        QtWidgets.QMessageBox.information(self, 'Stopped', 'Measurement stopped.')
        self.lcdNumber.display(0)
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

    def check_input(self):
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
                self.textEdit_status.setText("%s%d" % (status, int(value)))
            except (ValueError, UnboundLocalError):
                errors.append("Status has to be either 'pre' or 'post' followed by an integer.")

        # do we have errors? warn the user!
        if len(errors):
            QtWidgets.QMessageBox.critical(self, 'Error', "\n".join(errors))
            return False
        # if not, everything is fine
        return True


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = LoadAndPlayKonfig()
    ex.show()
    app.exec_()


def test():
    app = QtWidgets.QApplication(sys.argv)
    ex = LoadAndPlayKonfig()
    ex.textEdit_Experimenter.setText("Achim")
    ex.textEdit_Mousname.setText("TestMouse")
    ex.lineEdit_Path.setText(r"GUI Playlist/ein test_HEARINGTHRESHOLD.npy")
    ex.textEdit_status.setText("pre10")
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
