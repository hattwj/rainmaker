#!/usr/bin/env python
import sys
from PyQt4 import QtCore, QtGui


class CustomWidget(QtGui.QLabel):
    signal_hided = QtCore.pyqtSignal()
    signal_shown = QtCore.pyqtSignal()
    def hideEvent(self, event):
        print 'hideEvent'
        super(CustomWidget, self).hideEvent(event)
        self.signal_hided.emit()

    def showEvent(self, event):
        print 'showEvent'
        super(CustomWidget, self).showEvent(event)
        self.signal_shown.emit()


class MainWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.widget1 = CustomWidget('Widget1')
        self.widget2 = CustomWidget('Widget2')

        # connect signals, so if one widget is hidden then other is shown
        self.widget1.signal_hided.connect(self.widget2.show)
        self.widget2.signal_hided.connect(self.widget1.show)
        self.widget2.signal_shown.connect(self.widget1.hide)
        self.widget1.signal_shown.connect(self.widget2.hide)

        # some test code
        self.button = QtGui.QPushButton('test')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.widget1)
        layout.addWidget(self.widget2)
        self.setLayout(layout)
        self.button.clicked.connect(self.do_test)

    def do_test(self):
        if self.widget1.isHidden():
            self.widget1.show()
        else:
            self.widget2.show()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    widget = MainWidget()
    widget.resize(640, 480)
    widget.show()

    sys.exit(app.exec_())
