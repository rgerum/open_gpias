#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ConfigEditor.py

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
from open_gpias import gui_helpers
import sounddevice as sd


# add exception hook hack to prevent from python just crashing without throwing an exception, which occurs on some Qt5 installations
def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = my_excepthook

def file_iter(file):
    for line in file:
        yield line.strip()


config_filename = os.path.normpath(os.path.join(os.getenv('APPDATA'), "..", "Local", "OpenGPIAS", "config.txt"))


class Config:
    device = ""
    channels = [1, 2, 3]
    samplerate = 96000
    channel_latency = [0., 0., 14.8125, 14.8125]

    profile_loudspeaker_noise = ""
    profile_loudspeaker_burst = ""
    speaker_amplification_factor = [0.000019, 0.001 / 3200]

    recordingrate = 10000
    recording_device = "Dev2"

    output_directory = os.path.normpath(os.path.join(os.getenv('APPDATA'), "..", "..", "Desktop", "OpenGPIAS"))

    directory_backup = "Backup"
    directory_measurements = "Measurements"
    directory_protocols = "Protocols"

    acceleration_sensor_factors = [0.9027, 1.0, 3.8773]
    acceleration_sensor_sensitivity_v_to_g = 0.300
    acceleration_threshold = 0.05

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
                tp = type(old_value[0])
                setattr(self, key, [tp(v.strip()) for v in value.split(",")])
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
            indexCombo = widget.findText(str(self.getValue(attr, index)))
            if indexCombo >= 0:
                widget.setCurrentIndex(indexCombo)
            else:
                self.setValue(attr, widget.currentText(), index)
            widget.currentTextChanged.connect(lambda text: self.setValue(attr, text, index))


class ConfigEditor(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
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
        try:
            self.config.load(config_filename)
        except FileNotFoundError:
            pass
        print(self.config)

        self.input_devices = gui_helpers.addComboBox(layout_main, "sound device:", device_names)
        self.config.connect(self.input_devices, "device")
        self.input_devices.currentTextChanged.connect(self.selectDevice)
        self.channel_count = 0
        self.channel_trigger = gui_helpers.addComboBox(layout_main, "channel trigger:", [])
        self.channel_noise = gui_helpers.addComboBox(layout_main, "channel pre-stimulus:", [])
        self.channel_burst = gui_helpers.addComboBox(layout_main, "channel startle-stimulus:", [])

        self.input_samplerate = gui_helpers.addSpinBox(layout_main, "sample rate (Hz):", 96000, 44100, 100000, step=1000)
        self.config.connect(self.input_samplerate, "samplerate")

        self.input_channel_latency = gui_helpers.addLineEdit(layout_main, "channel latency (ms):", "0, 0, 14.8125, 14.8125", "0, 0, 14.8125, 14.8125")
        self.config.connect(self.input_channel_latency, "channel_latency")

        self.input_speaker_amplification_factor = gui_helpers.addLineEdit(layout_main, "speaker amplification factor:",
                                                             "0.001, 0.001", "")
        self.config.connect(self.input_speaker_amplification_factor, "speaker_amplification_factor")

        self.input_profile_noise = gui_helpers.addFileChooser(layout_main, "equalizer profile loudspeaker pre-stimulus:", "", "*.npy")
        self.config.connect(self.input_profile_noise, "profile_loudspeaker_noise")

        self.input_profile_burst = gui_helpers.addFileChooser(layout_main, "equalizer profile loudspeaker startle-stimulus:", "", "*.npy")
        self.config.connect(self.input_profile_burst, "profile_loudspeaker_burst")

        self.input_recording_device = gui_helpers.addLineEdit(layout_main, "recording device:", "Dev0", "")
        self.config.connect(self.input_recording_device, "recording_device")

        self.input_recordingrate = gui_helpers.addSpinBox(layout_main, "recording rate (Hz):", 10000, 1000, 100000, step=1000)
        self.config.connect(self.input_recordingrate, "recordingrate")

        self.input_acceleration_sensor_factors = gui_helpers.addLineEdit(layout_main, "acceleration sensor factors:",
                                                             "0, 0, 0", "")
        self.config.connect(self.input_acceleration_sensor_factors, "acceleration_sensor_factors")

        self.input_acceleration_sensor_sensitivity = gui_helpers.addLineEdit(layout_main, "acceleration sensor sensitivity (mV/g):", "0.300")
        self.config.connect(self.input_acceleration_sensor_sensitivity, "acceleration_sensor_sensitivity_v_to_g")

        self.input_acceleration_threshold = gui_helpers.addLineEdit(layout_main, "acceleration threshold (g):", "0.05")
        self.config.connect(self.input_acceleration_threshold, "acceleration_threshold")

        layout_buttons = QtWidgets.QHBoxLayout()
        layout_main.addLayout(layout_buttons)
        self.button_save = gui_helpers.addPushButton(layout_buttons, "Save", self.save, icon=qta.icon("fa.save"))
        self.button_save = gui_helpers.addPushButton(layout_buttons, "Cancel", self.close)
        self.selectDevice()

        self.config.connect(self.channel_trigger, "channels", 0)
        self.config.connect(self.channel_noise, "channels", 1)
        self.config.connect(self.channel_burst, "channels", 2)

        layout_main.addStretch()

    def save(self):
        directory = os.path.dirname(config_filename)
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.config.save(config_filename)
        if self.parent:
            self.parent.settingsUpdated.emit()

    def selectDevice(self):
        device_name = self.input_devices.currentText()
        i = -1
        first_valid_id = None
        for i in range(1000):
            i += 1
            try:
                name = sd.query_devices(i)["name"]
                if first_valid_id is None:
                    first_valid_id = i
            except sd.PortAudioError:
                continue
            if name == device_name:
                break
        else:
            i = first_valid_id
        channels = sd.query_devices(i)["max_output_channels"]
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
