import wx
import wx.xrc as xrc

class App(wx.App):

  def __init__(self):
    '''Constructor.'''
    wx.App.__init__(self)

    def OnInit(self):
        self.xrc = xrc.XmlResource('rainmaker_gui.xrc')
        self.dialog_fpicker = self.xrc.LoadFrame(None,'dialog_fpicker')
        self.dialog_fpicker.Show()
        return True
def main():
    app = App()
    app.MainLoop()
if __name__ == '__main__':
    main()
