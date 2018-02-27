# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 12:56:07 2017

@author: richard
"""

import os
import sys
import time
import numpy as np
from qtpy import QtCore, QtGui, QtWidgets
from asr_setup import gui_helpers, soundSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pandas as pd


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

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Acoustic Startle Response - Signal Editor")
        self.parent = parent

        layout_main = QtWidgets.QVBoxLayout(self)

        if 0:
            self.input_signal = gui_helpers.addLineEdit(layout_main, "Signal:", "...", "")
            self.input_signal.textEdited.connect(self.updateSignal)
            self.input_signal.setText("silence(30)pureTone(1000, 30)silence(70)")
            self.input_signal2 = gui_helpers.addLineEdit(layout_main, "Signal2:", "...", "")
            self.input_signal2.textEdited.connect(self.updateSignal)
            self.input_signal2.setText("silence(130)noiseBurst()")
        else:
            self.input_protocol_file = gui_helpers.addFileChooser(layout_main, "Protocol file:", "", "byteType (*_HEARINGTHRESHOLD.npy *_TURNER.npy *_TURNER_AND_HEARINGTHRESHOLD.npy)")
            self.input_protocol_file.textEdited.connect(self.updateProtocolFile)

        self.figure = plt.figure("signal")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout_main.addWidget(self.canvas)
        layout_main.addWidget(self.toolbar)

        self.ax1 = self.figure.add_subplot(3, 1, 1)
        self.ax2 = self.figure.add_subplot(3, 1, 2, sharex=self.ax1)
        self.ax3 = self.figure.add_subplot(3, 1, 3, sharex=self.ax1)
        self.axes = [self.ax1, self.ax2, self.ax3]

        self.signal = soundSignal.Signal(None)
        self.play_list_index = 0

        layout_main.addStretch()

    def checkProtocol(self):
        if self.protocol is None:
            return False, "No valid protocol file loaded."
        return True, "Protocol with %d runs loaded" % len(self.protocol)

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

        self.play_list_index = 0
        header = ["noiseIDX", "noiseGapIDX", "noiseFreqMinIDX", "noiseFreqMaxIDX", "preStimSPL_IDX", "preStimFreqIDX",
                  "ISIIDX", "noiseTimeIDX"]
        pd.set_option('expand_frame_repr', False)
        df = pd.DataFrame(self.protocol.astype("int"), columns=header)
        print(df)
        self.plotOutputSignal()

        if self.parent:
            self.parent.settingsUpdated.emit()

    def plotOutputSignal(self):
        thisKonfig = self.protocol[self.play_list_index]
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
        for ax in self.axes:
            ax.cla()
        x = np.arange(matrixToPlay.shape[0]) / self.signal.SAMPLE_RATE
        x = x - x[-1]
        colors = ["C0", "C2", "C3"]
        for index, i in enumerate([0, 2, 3]):
            ax = self.axes[index]
            if index == 0:
                ax.set_title("Run %d/%d" % (self.play_list_index+1, len(self.protocol)))
            ax.plot(x, matrixToPlay[:, i], color=colors[index])
            ax.set_xlim(x[-1]-1, x[-1])
            ax.grid(True)
        self.ax1.set_ylabel("trigger pulse")
        self.ax2.set_ylabel("pre-pulse")
        self.ax3.set_ylabel("startle pulse")
        ax.set_xlabel("time (s)")
        self.canvas.draw()

    def keyPressEvent(self, event):
        print(event.key())
        if event.key() == QtCore.Qt.Key_A:
            self.play_list_index = max(self.play_list_index - 1, 0)
            self.plotOutputSignal()
        if event.key() == QtCore.Qt.Key_D:
            self.play_list_index = min(self.play_list_index + 1, self.protocol.shape[0] - 1)
            self.plotOutputSignal()

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
