from PyQt4 import QtGui, QtCore

from rmmain import *
import framebasic
import frameadv

import sys

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class fbasic(framebasic.Ui_Frame):
    #def __init__(self):
    #    pass
    #    #self.frame = QtGui.QFrame(parent)
    #    #self.setupUi(self.frame) 
    #    pass

    def setupUi(self,Frame):
        super(fbasic,self).setupUi(Frame)
        print 999       
        QtCore.QObject.connect(self.btn_local_root, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_btn_local_root)

    def on_btn_local_root(self):
       print 'test'
       dialog = DirDialog() 
       path=dialog.show() 
       print path

class DirDialog(QtGui.QFileDialog):
    def __init__(self, parent=None):
        QtGui.QFileDialog.__init__(self, parent)

    def show (self):
        dialog = QtGui.QFileDialog.getExistingDirectory(self, 
            "Open Directory",
            "",
            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)

        return dialog 



class myGui(Ui_MainWindow):
    #sig_close = pyqtSignal()
    def __init__(self):
        self.MainWindow = QtGui.QMainWindow()
        self.setupUi(self.MainWindow)
        
        fb = fbasic()
        #self.frame_basic = fbasic( self.scrollAreaWidgetContents )
        self.frame_basic = QtGui.QFrame(self.scrollAreaWidgetContents)
        fb.setupUi( self.frame_basic )

        self.horizontalLayout_5.addWidget(self.frame_basic)

        
        QtCore.QObject.connect(self.btn_new, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_frame_new_show)
        QtCore.QObject.connect(self.btn_status, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_frame_status_show)
        QtCore.QObject.connect(self.btn_close, QtCore.SIGNAL(_fromUtf8("clicked()")), self.MainWindow.close)

        self.frame_basic.hide()
        self.cur_frame = self.frame_status
        self.MainWindow.show()

        #self.sig_close.connect(self.slot_close)
        #self.btn_close.clicked.connect(self.on_btn_close)

    def on_frame_new_show(self):
        self.frame_show( self.frame_basic )
        #self.frame_status.hide()
        #self.frame_basic.show()
        self.btn_new.setDisabled(True)
        self.btn_status.setEnabled(True)
        self.btn_config.setEnabled(True)

    def on_frame_status_show(self):
        self.frame_show( self.frame_status )
        #self.frame_basic.hide()
        #self.frame_status.show()
        self.btn_new.setEnabled(True)
        self.btn_config.setEnabled(True)
        self.btn_status.setDisabled(True)

    def frame_show(self,new_frame):
        self.cur_frame.hide()
        self.cur_frame = new_frame
        self.cur_frame.show()

    #def slot_close(self):
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    f = myGui()
    sys.exit(app.exec_() )
