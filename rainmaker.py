import sys 
import wx
import os
import time
import fsmon
import watcher
#import yaml
"""
manages all taskbar icon activity
"""
class TaskBarIcon(wx.TaskBarIcon):  

    def __init__(self, parent):
        print "TaskBarIcon:__init__()"
        wx.TaskBarIcon.__init__(self)  
        self.parentApp = parent  
        self.icons = {}
        self.CreateMenu()  
    def LoadIcons(self,files):
        for f in files:
            self.icons[f] = wx.Icon(files[f]['file'], wx.BITMAP_TYPE_PNG)         
    def CreateMenu(self):
        print "TaskBarIcon:CreateMenu()"
        #Create menu and bind its creation to a. right click on the taskbar icon
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.ShowMenu)  
        self.menu=wx.Menu()
        self.menu.Append(wx.ID_PREFERENCES, "Settings"," View Configuration and Status")
        self.menu.Append(wx.ID_ABOUT, "About"," Information about this program")
        self.menu.AppendSeparator()
        self.menu.Append(wx.ID_EXIT, "Exit")
        #Register event Handlers for menu entries
        wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, wx.ID_PREFERENCES, self.OnPreferences)
        #wx.ID_EXIT doesnt need an event handler
    def ShowMenu(self,event):
        print "TaskBarIcon:ShowMenu()"
        #Create popup menu for taskbar
        self.PopupMenu(self.menu)  
    def OnAbout(self,event):
        print "TaskBarIcon:OnAbout()"
        #create about dialog
        self.parentApp.OnAbout(event)
    def OnPreferences(self,event):
        print "TaskBarIcon:OnPreferences()"
        #create preferences (Settings) dialog
        self.parentApp.OnPreferences(event)
    def SetIconImage(self, status,msg=''):
        print "TaskBarIcon:SetIconImage()"
        # has_key(status)
        if self.icons.has_key(status):  # successful sync, everything up to date
            self.SetIcon(self.icons[status], msg)  
        else: # Unknown error
            self.SetIcon(self.icons[99], msg)  
"""
the main configuration screen
"""
class SettingsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        self.parent = parent
        # Create form
        wx.Frame.__init__(self, parent, -1, title, size = (600, 400),
        style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        filename = 'default.prf'
        lbl_str= "Unison Config: "+filename
        self.lbl_prf = wx.StaticText(self, -1, lbl_str , wx.Point(30, 30))

        # Create controls
        outputBoxID = wx.NewId()
        self.outputBox = wx.TextCtrl(self, outputBoxID, style=wx.TE_MULTILINE|wx.HSCROLL)
        self.btn_close = wx.Button(self, id=wx.ID_ANY, label="Close")
        self.btn_save = wx.Button(self, id=wx.ID_ANY, label="Save")
        self.btn_save.Disable()
        
        # Basic control layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.lbl_prf, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.outputBox, 6, wx.EXPAND | wx.ALL | wx.TE_READONLY, 10)
        #sizer.Add(self.btn_save, flag=wx.LEFT, border=10)
        #sizer.Add(self.btn_close, flag=wx.RIGHT, border=10)
        
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        sizer_h.Add(self.btn_save, flag=wx.LEFT, border=10)
        sizer_h.Add(self.btn_close, flag=wx.RIGHT, border=10)
        sizer.Add(sizer_h, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(sizer)
        
        # Load Config Data
        self.uni_prf = '/home/hattb/.unison/default.prf'
        self.outputBox.LoadFile( self.uni_prf )
        
        # Bind Events
        self.outputBox.Bind(wx.EVT_TEXT, self.OnText) 
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnButton)
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
    def OnText(self,event):
        if not self.outputBox.IsModified():
            self.btn_save.Disable()
        else:
            self.btn_save.Enable()
    def OnButton(self,event):
        if self.outputBox.IsModified():
            self.outputBox.SaveFile( self.uni_prf )
            #self.parent.StartUnison()
    def OnClose(self,event):
        self.Close(True)
"""
the main portion of the application
-controls all other activity
"""
import sub_proc
class MainAppFrame(wx.Frame):  

    def __init__(self, parent, id, title):
        print "MainAppFrame:__init__()"
        wx.Frame.__init__(self, parent, -1, title, size = (1, 1),  
            style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)  

    def OnAbout(self,event):
        print "MainAppFrame:OnAbout()"
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog( self,"""rainmaker is a small gui wrapper for Unison that hopes to deliver functionality similar to dropbox, but with more customizability.
        """, "rainmaker", wx.OK)
        dlg.ShowModal()      # Show it
        dlg.Destroy()        # finally destroy it when finished.

    def OnPreferences(self,event):
        print "MainAppFrame:OnPreferences()"
        prefs_form = SettingsFrame(self, -1, "rainmaker")
        prefs_form.Show(True)

    def DoConfig(self):
        print "MainAppFrame:DoConfig()"
        self.prefs = RainConfigure()
        self.tbicon = TaskBarIcon(self)
        self.tbicon.LoadIcons(self.prefs.icons)
        self.tbicon.Bind(wx.EVT_MENU, self.exitApp, id=wx.ID_EXIT)   
        self.Show(True)
        # display init icon
        self.tbicon.SetIconImage(90)

    def StartMonitor(self):
        print "MainAppFrame:StartMonitor()"
        # display initial sync icon
        self.tbicon.SetIconImage(91)
        
        # Start Monitoring File System
        self.fsmonitor = watcher.UnisonWatcher(self.prefs.unison)
        self.tbicon.SetIconImage(0)
        
        # Start Timer
        self.timer_poll = wx.Timer(self)
        self.timer_poll.Start(5000) # look every 5 seconds for events
        self.Bind(wx.EVT_TIMER, self.PollMonitor, self.timer_poll)

    def PollMonitor(self, event):
        print "MainAppFrame:PollMonitor()"
        # Check FS monitor for changes
        result = self.fsmonitor.update()
        print result
        msg = self.prefs.icons[98]['msg']
        self.tbicon.SetIconImage(98,msg)

    def exitApp(self,event):
        print "MainAppFrame:exitApp()"
        self.tbicon.RemoveIcon()  
        self.tbicon.Destroy()  
        self.fsmonitor.stop()
        sys.exit()
        
class RainConfigure():
    unison = {'app_dir': '.rainmaker',
        'app_name': 'rainmaker',
        'app_about': """rainmaker is a small gui wrapper for Unison that hopes to deliver functionality similar to dropbox, but with more customizability.""",
        'root_local': '/home/hattb/sync',
        'root_remote': '/home/rainmaker/users/hattb/sync',
        'key_path': '/home/hattb/.ssh/id_dsa',
        'unison_path': '/usr/bin/unison',
        'unison_prf': 'default1'
    }
# starting full sync of roots
# authenticating with server
    icons = {
        0:{'file':'code-0.png','msg':'Transfer Successfull'},
        1:{'file':'code-1.png','msg':'Some conflicts exist...'},
        2:{'file':'code-2.png','msg':'Non fatal error occurred'},
        3:{'file':'code-3.png','msg':'Fatal error occurred'},
        90:{'file':'code-90.png','msg':'Initializing...'},
        91:{'file':'code-91.png','msg':'Contacting Server...'},
        98:{'file':'code-98.png','msg':'Unable to contact Server...'},
        99:{'file':'code-99.png','msg':'Unknown event occurred'}
    }
    """
    def __init__(self):
        self.homedir = os.path.expanduser('~')
        self.app_path = os.path.join(self.homedir,self.app_dir)
        print self.homedir
        print self.app_path
        
        #Try to create directory
        try:
            if not os.path.exists(self.app_path) or not os.path.isdir(self.app_path):
                os.makedirs(self.app_path)
        except OSError:
            print "Unable to create directory: "+self.app_path
            sys.exit()
        
        #Try to load config file
        self.abs_app_config = os.path.join( self.app_path, self.app_config )
        if os.path.isfile( self.abs_app_config  ):
            self.load_config()
        else:
            self.create_config()
    def create_config():
        self.config = { 'unison_app':'',
                        'osd_type':'',
                        'unison_pref':''}
        f = open('newtree.yaml', "w")
        #yaml.dump(self.abs_app_config, f)
        f.close()
    def load_config():
        pass"""
#---------------- run the program -----------------------  
def main(argv=None):
    print "main:wx.App()"
    app = wx.App(False)
    print "main:MainAppFrame()"
    frame = MainAppFrame(None, -1, ' ')
    print "main:DoConfig()"
    frame.DoConfig()
    print "main:StartMonitor()"
    frame.StartMonitor()
    print "main:frame.Show()"
    frame.Show(False)
    print "main:wx.MainLoop()"
    app.MainLoop()  
    
if __name__ == '__main__':  
    main()
