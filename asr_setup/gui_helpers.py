from qtpy import QtCore, QtGui, QtWidgets

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


def addPushButton(layout, name, function):
    button = QtWidgets.QPushButton(name)
    button.clicked.connect(function)
    layout.addWidget(button)
    return button

def addLabel(layout, name):
    label = QtWidgets.QLabel(name)
    layout.addWidget(label)

def addLineEdit(layout, name, placeholder):
    addLabel(layout, name)

    edit = QtWidgets.QLineEdit()
    edit.setPlaceholderText(placeholder)
    layout.addWidget(edit)
    return edit

def addTextBox(layout, name):
    addLabel(layout, name)

    edit = QtWidgets.QTextEdit()
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
