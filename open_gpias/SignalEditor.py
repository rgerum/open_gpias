#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SignalEditor.py

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
from open_gpias import gui_helpers, soundSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pandas as pd
from open_gpias.playlist import FrontendPlaylist


# add exception hook hack to prevent from python just crashing without throwing an exception, which occurs on some Qt5 installations
def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = my_excepthook


# Indices to access the config array
# Need To match indices of BackendPlaylist
noiseIDX = 0
noiseGapIDX = 1
noiseFreqMinIDX = 2
noiseFreqMaxIDX = 3
preStimAttenIDX = 4
preStimFreqIDX = 5
ISIIDX = 6
noiseTimeIDX = 7


class SignalEditor(QtWidgets.QWidget):
    turner = False
    hearingThreshold = False
    protocol = None
    error = ""

    def __init__(self, parent=None, config=None, signal=None):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Signal Editor")
        self.parent = parent
        self.config = config

        layout_main = QtWidgets.QVBoxLayout(self)

        gui_helpers.addPushButton(layout_main, "new protocol", self.openProtocolCreator)

        if 0:
            self.input_signal = gui_helpers.addLineEdit(layout_main, "Signal:", "...", "")
            self.input_signal.textEdited.connect(self.updateSignal)
            self.input_signal.setText("silence(30)pureTone(1000, 30)silence(70)")
            self.input_signal2 = gui_helpers.addLineEdit(layout_main, "Signal2:", "...", "")
            self.input_signal2.textEdited.connect(self.updateSignal)
            self.input_signal2.setText("silence(130)noiseBurst()")
        else:
            self.input_protocol_file = gui_helpers.addFileChooser(layout_main, "Protocol file:", os.path.join(self.config.output_directory, self.config.directory_protocols), "byteType (*_HEARINGTHRESHOLD.npy *_TURNER.npy *_TURNER_AND_HEARINGTHRESHOLD.npy)")
            self.input_protocol_file.textEdited.connect(self.updateProtocolFile)

        layout_navigate = QtWidgets.QHBoxLayout(self)
        layout_main.addLayout(layout_navigate)
        gui_helpers.addPushButton(layout_navigate, "", self.navigateLeft, icon=qta.icon("fa.arrow-left"))
        self.label_title = QtWidgets.QSpinBox()
        self.label_title.setSuffix(" / 0")
        self.label_title.setPrefix("Trial ")
        self.label_title.setRange(0, 0)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.label_title.valueChanged.connect(self.plotOutputSignal)
        layout_navigate.addWidget(self.label_title)
        gui_helpers.addPushButton(layout_navigate, "", self.navigateRight, icon=qta.icon("fa.arrow-right"))

        self.figure = plt.figure("signal")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout_main.addWidget(self.canvas)
        layout_main.addWidget(self.toolbar)

        self.ax1 = self.figure.add_subplot(3, 1, 1)
        self.ax2 = self.figure.add_subplot(3, 1, 2, sharex=self.ax1)
        self.ax3 = self.figure.add_subplot(3, 1, 3, sharex=self.ax1)
        self.axes = [self.ax1, self.ax2, self.ax3]

        self.preparePlot()

        if signal is not None:
            self.signal = signal
        else:
            self.signal = soundSignal.Signal(self.config)
        self.parent.settingsUpdated.connect(self.signal.loadConfig)
        self.play_list_index = 0

        layout_main.addStretch()

    def openProtocolCreator(self):
        path = os.path.join(self.config.output_directory, self.config.directory_protocols)
        if not os.path.exists(path):
            os.makedirs(path)
        FrontendPlaylist.PlaylistGenerator(path)

    def checkProtocol(self):
        if self.protocol is None:
            return False, "No valid protocol file loaded."
        return True, "Protocol with %d runs loaded" % len(self.protocol)

    def navigateLeft(self):
        self.label_title.stepDown()

    def navigateRight(self):
        self.label_title.stepUp()

    def updateProtocolFile(self):
        self.protocol = None
        filename = self.input_protocol_file.text()
        # try to load the config file
        try:
            protocolFile = open(filename, "rb")
        except IOError:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'The specified config file cannot be loaded.')
            return

        # check the content of the config file
        protocol = np.load(protocolFile, allow_pickle=False, fix_imports=False)
        if filename.endswith("_TURNER.npy"):
            self.turner = True
            self.hearingThreshold = False

            for a in protocol[5:]:
                if a[4] != 0 or a[5] != 0 or a[6] != 0 or len(a) != 8:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        elif filename.endswith("_TURNER_AND_HEARINGTHRESHOLD.npy"):
            self.turner = True
            self.hearingThreshold = True
            for a in protocol:
                if len(a) != 8:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        elif filename.endswith("_HEARINGTHRESHOLD.npy"):
            self.turner = False
            self.hearingThreshold = True
            for a in protocol:
                if a[0] != 0 or a[1] != 0 or a[2] != 0 or a[3] != 0:
                    QtWidgets.QMessageBox.warning(self, 'Warning', 'The loaded config file is corrupted.')
                    raise RuntimeError
        else:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'The name of the config file does not match.')
            raise RuntimeError

        self.protocol = protocol
        self.label_title.setRange(1, len(self.protocol))
        self.label_title.setSuffix(" / %d" % len(self.protocol))

        self.play_list_index = 0
        header = ["noiseIDX", "noiseGapIDX", "noiseFreqMinIDX", "noiseFreqMaxIDX", "preStimSPL_IDX", "preStimFreqIDX",
                  "ISIIDX", "noiseTimeIDX"]
        pd.set_option('expand_frame_repr', False)
        df = pd.DataFrame(self.protocol.astype("int"), columns=header)
        print(df)
        self.plotOutputSignal()

        if self.parent:
            self.parent.settingsUpdated.emit()

    def getProtocolName(self):
        if self.turner and self.hearingThreshold:
            fileNameEnding = "_turner_and_threshold"
        elif self.turner:
            fileNameEnding = "_turner"
        elif self.hearingThreshold:
            fileNameEnding = "_threshold"
        return fileNameEnding

    def plotOutputSignal(self):
        thisKonfig = self.protocol[self.label_title.value()-1]
        noise = thisKonfig[noiseIDX]
        noiseGap = thisKonfig[noiseGapIDX]
        noiseFreqMin = thisKonfig[noiseFreqMinIDX]
        noiseFreqMax = thisKonfig[noiseFreqMaxIDX]
        preStimAtten = thisKonfig[preStimAttenIDX]
        preStimFreq = thisKonfig[preStimFreqIDX]
        ISI = thisKonfig[ISIIDX]
        noiseTime = thisKonfig[noiseTimeIDX]
        print("noiseGap", noiseGap)
        if noise:
            matrixToPlay, result = self.signal.gpiasGap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise,
                                                        doGap=noiseGap)
        else:
            matrixToPlay, result = self.signal.asrPrepuls(preStimFreq, preStimAtten, ISI, prepulse=preStimAtten >= 0)

        x = np.arange(matrixToPlay.shape[0]) / self.signal.SAMPLE_RATE
        x = x - x[-1]
        for index, i in enumerate(self.config.channels):  # TODO load correct channels
            self.plots[index].set_data(x, matrixToPlay[:, i-1])
            self.axes[index].set_xlim(x[-1]-1, x[-1])
            self.axes[index].set_ylim(-np.max(np.abs(matrixToPlay[:, i-1]))*1.1, np.max(np.abs(matrixToPlay[:, i-1]))*1.1)
        self.canvas.draw()

    def preparePlot(self):
        for ax in self.axes:
            ax.cla()
        colors = ["C0", "C2", "C3"]
        self.plots = []
        for index, i in enumerate([0, 2, 3]):
            ax = self.axes[index]
            p1, = ax.plot([0, 0], [0, 0], color=colors[index])
            self.plots.append(p1)
            ax.grid(True)
        self.ax1.set_ylabel("trigger pulse")
        self.ax2.set_ylabel("pre-pulse")
        self.ax3.set_ylabel("startle pulse")
        ax.set_xlabel("time (s)")
        self.canvas.draw()

    def keyPressEvent(self, event):
        print(event.key())
        if event.key() == QtCore.Qt.Key_A:
            self.navigateLeft()
        if event.key() == QtCore.Qt.Key_D:
            self.navigateRight()

    def processSignal(self, text):
        output = np.zeros((0))
        commands = text.split(")")
        for command in commands:
            # remove white space
            command = command.strip()
            # ignore if it is an empty string
            if len(command) == 0:
                continue
            # split function name and parameters
            func, parameters = command.split("(")

            # generate a list from the parameters
            if len(parameters.strip()):
                parameters = [float(x) for x in parameters.split(",")]
            else:
                parameters = []

            # call the function
            output2 = getattr(self.signal, func)(*parameters)
            output = np.hstack((output, output2))
        return output

    def updateSignal(self):

        output1 = self.processSignal(self.input_signal.text())
        output2 = self.processSignal(self.input_signal2.text())

        self.figure.clf()
        x = np.arange(0, len(output1))/self.signal.SAMPLE_RATE
        plt.plot(x, output1)
        x = np.arange(0, len(output2))/self.signal.SAMPLE_RATE
        plt.plot(x, output2)
        plt.xlabel("time (s)")
        plt.ylabel("sound pressure level")
        plt.grid(True)
        self.canvas.draw()

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = SignalEditor()
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
