import os
import sys
import ctypes
from qtpy import QtCore, QtGui, QtWidgets
import qtawesome as qta
from .ConfigEditor import ConfigEditor
from .SignalEditor import SignalEditor
from .StimulusFrontEnd import measurementGui
from .soundSignal import Signal


class mainWindow(QtWidgets.QWidget):
    settingsUpdated = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("OpenGPIAS")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icon.ico")))
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.configEditor = ConfigEditor(self)
        self.config = self.configEditor.config
        self.signal = Signal(self.config)
        self.protocolEditor = SignalEditor(self, self.config, self.signal)
        self.measurementGui = measurementGui(self, self.protocolEditor, self.config, self.signal)

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.addTab(self.configEditor, qta.icon("fa.cogs"), "Config")
        self.tabWidget.addTab(self.protocolEditor, qta.icon("fa.calendar-o"), "Protocol")
        self.tabWidget.addTab(self.measurementGui, qta.icon("fa.volume-up"), "Measure")
        self.layout.addWidget(self.tabWidget)


def main():
    app = QtWidgets.QApplication(sys.argv)
    # set an application id, so that windows properly stacks them in the task bar
    if sys.platform[:3] == 'win':
        myappid = 'schilling.opengpias'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ex = mainWindow()
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
