from qtpy import QtCore, QtGui, QtWidgets
import qtawesome as qta
import datetime

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

        self.editingFinished = self.lineEdit.editingFinished
        self.textEdited = self.lineEdit.textEdited

    def selectFile(self):
        self.lineEdit.setText(QtWidgets.QFileDialog.getOpenFileName(directory=self.directory, filter=self.filter)[0])
        self.textEdited.emit(self.lineEdit.text())

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)


class QStatus(QtWidgets.QLabel):
    def __init__(self, status, layout=None):
        super().__init__()
        self.setStatus(status)
        if layout is not None:
            layout.addWidget(self)

    def setStatus(self, value):
        if isinstance(value, tuple):
            self.setToolTip(value[1])
            value = value[0]
        self.status = value
        if self.status:
            self.setPixmap(qta.icon("fa.check", color="green").pixmap(16))
        else:
            self.setPixmap(qta.icon("fa.close", color="red").pixmap(16))


class QStatusBar(QtWidgets.QWidget):
    def __init__(self, properties, layout=None):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.statusWidgets = {}
        for key in properties:
            label = QtWidgets.QLabel(key)
            self.layout.addWidget(label)
            self.statusWidgets[key] = QStatus(properties[key], self.layout)
        if layout is not None:
            layout.addWidget(self)

    def setStatus(self, status):
        for key in status:
            self.statusWidgets[key].setStatus(status[key])


class QLogWidget(QtWidgets.QTextEdit):
    log_texts = ""

    def __init__(self, layout=None):
        super().__init__()
        self.setReadOnly(True)
        if layout is not None:
            layout.addWidget(self)

    def addLog(self, status):
        status = str(datetime.datetime.now()).split(".")[0]+" - "+status+"\n"
        self.log_texts += status

        # add the log text to the logfile
        log_filename = os.path.join(os.getenv('APPDATA'), "Open_GPIAS", time.strftime("%Y-%m")+"_log.txt")
        with open(log_filename, "a") as fp:
            fp.write(status)

        self.setText(self.log_texts)
        # scroll down
        c = self.textCursor()
        c.movePosition(QtGui.QTextCursor.End)
        self.setTextCursor(c)


def addPushButton(layout, name, function, icon=None):
    button = QtWidgets.QPushButton(name)
    button.clicked.connect(function)
    if icon is not None:
        button.setIcon(icon)
    layout.addWidget(button)
    return button

def addLabel(layout, name):
    label = QtWidgets.QLabel(name)
    layout.addWidget(label)

def addLineEdit(layout, name, placeholder, text=""):
    addLabel(layout, name)

    edit = QtWidgets.QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setText(text)
    layout.addWidget(edit)
    return edit

def addTextBox(layout, name):
    addLabel(layout, name)

    edit = QtWidgets.QTextEdit()
    layout.addWidget(edit)
    return edit

def addLogBox(layout, name):
    addLabel(layout, name)

    edit = QLogWidget()
    layout.addWidget(edit)
    return edit

def addFileChooser(layout, name, directory, types):
    addLabel(layout, name)

    edit = QFileChooseEdit(directory, types)
    layout.addWidget(edit)
    return edit

def addLCDNumber(layout, name):
    addLabel(layout, name)

    edit = QtWidgets.QLCDNumber()
    edit.display(0)
    layout.addWidget(edit)
    return edit


def addComboBox(layout, name, values):
    addLabel(layout, name)

    edit = QtWidgets.QComboBox()
    edit.addItems(values)
    layout.addWidget(edit)
    return edit

def addSpinBox(layout, name, value, min=0, max=100000, step=1):
    addLabel(layout, name)

    edit = QtWidgets.QSpinBox()
    edit.setRange(min, max)
    edit.setSingleStep(step)
    edit.setValue(value)
    layout.addWidget(edit)
    return edit
