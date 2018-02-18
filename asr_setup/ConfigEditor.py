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
from . import gui_helpers
import sounddevice as sd


# add exception hook hack to prevent from python just crashing without throwing an exception, which occurs on some Qt5 installations
def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = my_excepthook


class ConfigEditor(QtWidgets.QWidget):
    timeString = ""
    shutDown = 0
    thisplot = None
    backup_plot_count = 0

    measurement_thread = None
    plot_window = None

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Configuration")

        layout_main = QtWidgets.QVBoxLayout(self)

        device_names = []
        for i in range(255):
            try:
                device = sd.query_devices(i)
            except sd.PortAudioError:
                break
            if device["max_output_channels"] > 0:
                device_names.append(device["name"])

        self.input_devices = gui_helpers.addComboBox(layout_main, "Sounddevice:", device_names)
        self.input_devices.currentTextChanged.connect(self.selectDevice)
        self.channel_count = 0
        self.channel_trigger = gui_helpers.addComboBox(layout_main, "Channel-Trigger:", [])
        self.channel_noise = gui_helpers.addComboBox(layout_main, "Channel-Noise:", [])
        self.channel_burst = gui_helpers.addComboBox(layout_main, "Channel-Burst:", [])
        self.input_samplerate = gui_helpers.addSpinBox(layout_main, "Sample Rate (Hz):", 96000, 44100, 100000, step=1000)
        self.input_channel_latency = gui_helpers.addLineEdit(layout_main, "Channel Latency (ms):", "0, 0, 14.8125, 14.8125", "0, 0, 14.8125, 14.8125")
        self.input_profile_noise = gui_helpers.addFileChooser(layout_main, "Profile Loudspeaker Noise:", "", "*.npy")
        self.input_profile_burst = gui_helpers.addFileChooser(layout_main, "Profile Loudspeaker Burst:", "", "*.npy")
        self.selectDevice()

    def selectDevice(self):
        device_name = self.input_devices.currentText()
        channels = sd.query_devices(device_name)["max_output_channels"]
        for i in range(self.channel_count, channels):
            for comboBox in [self.channel_trigger, self.channel_noise, self.channel_burst]:
                comboBox.addItems(["%d" % i])
        for i in np.arange(self.channel_count, channels, -1):
            for comboBox in [self.channel_trigger, self.channel_noise, self.channel_burst]:
                comboBox.removeItem(i)
        self.channel_count = channels


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = ConfigEditor()
    ex.show()
    app.exec_()


def test():
    app = QtWidgets.QApplication(sys.argv)
    ex = ConfigEditor()
    ex.textEdit_Experimenter.setText("Achim")
    ex.textEdit_Mousname.setText("TestMouse")
    ex.lineEdit_Path.setText(r"GUI Playlist/ein test_HEARINGTHRESHOLD.npy")
    ex.textEdit_status.setText("pre10")
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
