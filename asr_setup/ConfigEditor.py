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

def file_iter(file):
    for line in file:
        yield line.strip()


class Config:
    device = ""
    channels = [1, 2, 3]
    samplerate = 9600
    channel_latency = [0, 0, 0, 0]
    profile_loudspeaker_noise = ""
    profile_loudspeaker_burst = ""

    def load(self, filename):
        with open(filename, "r") as fp:
            file = file_iter(fp)
            for line in file:
                if line == "[sound]":
                    for line in file:
                        if line[0] == "[":
                            break
                        key, value = line.split("=", 1)
                        self.setValue(key, value)

    def save(self, filename):
        with open(filename, "w") as fp:
            fp.write("[sound]\n")
            attributes = [attr for attr in dir(self) if attr[0] != "_" and not callable(getattr(self, attr))]
            for attr in attributes:
                value = getattr(self, attr)
                if isinstance(value, list):
                    fp.write("%s=%s\n" % (attr, ",".join([str(i) for i in value])))
                else:
                    fp.write("%s=%s\n" % (attr, str(value)))

    def setValue(self, key, value, index=None):
        try:
            old_value = getattr(self, key)
        except AttributeError:
            print("Config file specified unknown field:", key, file=sys.stderr)
        else:
            if index is not None:
                old_value[index] = type(old_value[index])(value)
                return
            if isinstance(old_value, int):
                setattr(self, key, int(value))
            elif isinstance(old_value, list):
                setattr(self, key, [v.strip() for v in value.split(",")])
            else:
                setattr(self, key, value)

    def getValue(self, key, index=None):
        value = getattr(self, key)
        if index is not None:
            return value[index]
        if isinstance(value, list):
            return ",".join([str(i) for i in value])
        return str(value)

    def connect(self, widget, attr, index=None):
        if isinstance(widget, (QtWidgets.QLineEdit, gui_helpers.QFileChooseEdit)):
            widget.setText(self.getValue(attr))
            widget.textEdited.connect(lambda text: self.setValue(attr, text))
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(int(self.getValue(attr)))
            widget.valueChanged.connect(lambda text: self.setValue(attr, text))
        if isinstance(widget, QtWidgets.QComboBox):
            indexCombo = widget.findText(self.getValue(attr, index))
            if indexCombo >= 0:
                widget.setCurrentIndex(indexCombo)
            else:
                self.setValue(attr, widget.currentText(), index)
            widget.currentTextChanged.connect(lambda text: self.setValue(attr, text, index))


class ConfigEditor(QtWidgets.QWidget):

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

        self.config = Config()
        self.config.load("config.txt")
        print(self.config)

        self.input_devices = gui_helpers.addComboBox(layout_main, "Sounddevice:", device_names)
        self.config.connect(self.input_devices, "device")
        self.input_devices.currentTextChanged.connect(self.selectDevice)
        self.channel_count = 0
        self.channel_trigger = gui_helpers.addComboBox(layout_main, "Channel-Trigger:", [])
        self.channel_noise = gui_helpers.addComboBox(layout_main, "Channel-Noise:", [])
        self.channel_burst = gui_helpers.addComboBox(layout_main, "Channel-Burst:", [])

        self.input_samplerate = gui_helpers.addSpinBox(layout_main, "Sample Rate (Hz):", 96000, 44100, 100000, step=1000)
        self.config.connect(self.input_samplerate, "samplerate")

        self.input_channel_latency = gui_helpers.addLineEdit(layout_main, "Channel Latency (ms):", "0, 0, 14.8125, 14.8125", "0, 0, 14.8125, 14.8125")
        self.config.connect(self.input_channel_latency, "channel_latency")

        self.input_profile_noise = gui_helpers.addFileChooser(layout_main, "Profile Loudspeaker Noise:", "", "*.npy")
        self.config.connect(self.input_profile_noise, "profile_loudspeaker_noise")

        self.input_profile_burst = gui_helpers.addFileChooser(layout_main, "Profile Loudspeaker Burst:", "", "*.npy")
        self.config.connect(self.input_profile_burst, "profile_loudspeaker_burst")

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_main.addLayout(layout_buttons)
        self.button_save = gui_helpers.addPushButton(layout_buttons, "Save", self.save)
        self.button_save = gui_helpers.addPushButton(layout_buttons, "Cancel", self.close)
        self.selectDevice()

        self.config.connect(self.channel_trigger, "channels", 0)
        self.config.connect(self.channel_noise, "channels", 1)
        self.config.connect(self.channel_burst, "channels", 2)

    def save(self):
        self.config.save("config.txt")

    def selectDevice(self):
        device_name = self.input_devices.currentText()
        channels = sd.query_devices(device_name)["max_output_channels"]
        for i in range(self.channel_count, channels):
            for comboBox in [self.channel_trigger, self.channel_noise, self.channel_burst]:
                comboBox.addItems(["%d" % (i+1)])
        for i in np.arange(self.channel_count, channels-1, -1):
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
