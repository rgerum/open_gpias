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
from .ConfigEditor import ConfigEditor
from .SignalEditor import SignalEditor
from .StimulusFrontEnd import measurementGui

class mainWindow(QtWidgets.QWidget):
    settingsUpdated = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("OpenGPIAS")
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.configEditor = ConfigEditor(self)
        self.config = self.configEditor.config
        self.protocolEditor = SignalEditor(self)
        self.measurementGui = measurementGui(self, self.protocolEditor, self.config)

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.addTab(self.configEditor, qta.icon("fa.cogs"), "Config")
        self.tabWidget.addTab(self.protocolEditor, qta.icon("fa.calendar-o"), "Protocol")
        self.tabWidget.addTab(self.measurementGui, qta.icon("fa.volume-up"), "Measure")
        self.layout.addWidget(self.tabWidget)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = mainWindow()
    ex.show()
    app.exec_()


def test():
    app = QtWidgets.QApplication(sys.argv)
    ex = mainWindow()
    ex.textEdit_Experimenter.setText("Achim")
    ex.textEdit_Mousname.setText("TestMouse")
    ex.lineEdit_Path.setText(r"GUI Playlist/ein test_HEARINGTHRESHOLD.npy")
    ex.textEdit_status.setText("pre10")
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
