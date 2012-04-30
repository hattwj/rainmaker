from PyQt4 import QtGui, QtCore

from rmmain import *
import framebasic
import frameadv

import sys

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class myGui(Ui_MainWindow):
    #sig_close = pyqtSignal()
    def __init__(self):
        self.MainWindow = QtGui.QMainWindow()
        self.setupUi(self.MainWindow)
        
        fb = framebasic.Ui_Frame()
        self.frame_basic = QtGui.QFrame(self.scrollAreaWidgetContents)
        fb.setupUi( self.frame_basic )
        
        QtCore.QObject.connect(self.btn_new, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_frame_new_show)
        QtCore.QObject.connect(self.btn_status, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_frame_status_show)
        QtCore.QObject.connect(self.btn_close, QtCore.SIGNAL(_fromUtf8("clicked()")), self.MainWindow.close)

        self.frame_basic.hide()
        self.MainWindow.show()

        #self.sig_close.connect(self.slot_close)
        #self.btn_close.clicked.connect(self.on_btn_close)

    def on_frame_new_show(self):
        self.frame_status.hide()
        self.frame_basic.show()
        self.btn_new.setDisabled(True)
        self.btn_status.setEnabled(True)
        self.btn_config.setEnabled(True)

    def on_frame_status_show(self):
        self.frame_basic.hide()
        self.frame_status.show()
        self.btn_new.setEnabled(True)
        self.btn_config.setEnabled(True)
        self.btn_status.setDisabled(True)

    #def slot_close(self):
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    #w = QtGui.QMainWindow()
    f = myGui()
    #f.setupUi(w)
    #f.do_init()
    #app.setMainWidget(f)
    #w.show()
    sys.exit(app.exec_() )
    #app.exec_loop()
