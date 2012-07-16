import sys 
import wx
import os
import time
import fsmon
from watcher2 import *
#import yaml
"""
manages all taskbar icon activity
"""
class TaskBarIcon(wx.TaskBarIcon):  

    def __init__(self, parent):
        print "TaskBarIcon:__init__()"
        wx.TaskBarIcon.__init__(self)  
        self.parent = parent  
        self.icons = {}
        
        #Create menu and bind its creation to a. right click on the taskbar icon
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.ShowMenu)  
        self.menu=wx.Menu()

        self.CreateMenu()  
    def LoadIcons(self,files):
        for f in files:
            self.icons[f] = wx.Icon(files[f]['file'], wx.BITMAP_TYPE_PNG)

    def CreateMenu(self):
        print "TaskBarIcon:CreateMenu()"
        for item in self.menu.GetMenuItems():
            self.menu.DeleteItem(item)
        self.menu.Append(wx.ID_PREFERENCES, "Settings"," View Configuration and Status")
        if len(self.parent.event_handlers) > 0:
            self.menu.AppendSeparator()
            used_paths = []

            for event_handler in self.parent.event_handlers:
                # get path
                dir_path = event_handler.uconf['root']
                if dir_path not in used_paths:
                    used_paths.append(dir_path)
                else:
                    continue
                #Create one off function that will open the correct folder
                def OnBrowse(event,path=dir_path):
                    import subprocess
                    import sys
                    if sys.platform == 'darwin':
                        subprocess.check_call(['open', path])
                    elif sys.platform == 'linux2':
                        subprocess.check_call(['gnome-open', path])
                    elif sys.platform == 'windows':
                        subprocess.check_call(["explorer", path])
                        # I think you can call "explore" but I don't have a Windows
                        # computer up at the moment.
                # Create command event menu entry
                _id = wx.NewId()
                self.menu.Append(_id, "Show "+dir_path," Show Folder")
                wx.EVT_MENU(self, _id, OnBrowse)

        self.menu.AppendSeparator()
        self.menu.Append(wx.ID_ABOUT, "About"," Information about this program")
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
        self.parent.OnAbout(event)

    def OnPreferences(self,event):
        print "TaskBarIcon:OnPreferences()"
        #create preferences (Settings) dialog
        self.parent.OnPreferences(event)

    def SetIconImage(self, status,msg=''):
        #print "TaskBarIcon:SetIconImage()"
        # has_key(status)
        if self.icons.has_key(status):  # successful sync, everything up to date
            self.SetIcon(self.icons[status], msg)  
        else: # Unknown error
            self.SetIcon(self.icons[99], msg)  

########################################################################
class ProfilePanel(wx.Panel):

    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.txt = wx.TextCtrl(self)

class UnisonProfilePanel(wx.Panel):

    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.txt = wx.TextCtrl(self)

class StatusPanel(wx.Panel):
             
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent, size=(100,200))
        sizer = wx.GridSizer(rows=4, cols=2, hgap=1, vgap=1)
        txt1 = wx.TextCtrl(self)
        txt2 = wx.TextCtrl(self)
        txt3 = wx.TextCtrl(self)
        txt4 = wx.TextCtrl(self)
        txt5 = wx.TextCtrl(self)
        txt6 = wx.TextCtrl(self)
        txt7 = wx.TextCtrl(self)
        txt8 = wx.TextCtrl(self)


        sizer.Add(txt1, flag=wx.ALIGN_LEFT)
        sizer.Add(txt2, 0, 0)
        sizer.Add(txt3, 0, 0)
        sizer.Add(txt4, 0, 0)
        sizer.Add(txt5, 0, 0)
        sizer.Add(txt6, 0, 0)
        sizer.Add(txt7, 0, 0)
        sizer.Add(txt8, 0, 0)

        self.SetSizer(sizer) 

class EventPanel(wx.Panel):
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)

class NavPanel(wx.Panel):
             
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent, size=(120,200))
        self.parent = parent  
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn_1 = wx.Button(self, id=wx.ID_ANY, label="Status")
        self.btn_2 = wx.Button(self, id=wx.ID_ANY, label="New")
        self.btn_3 = wx.Button(self, id=wx.ID_ANY, label="Localhost")
        self.btn_close = wx.Button(self, id=wx.ID_ANY, label="Close")

        sizer.Add(self.btn_1, 1, wx.FIXED_MINSIZE, 10)
        sizer.Add(self.btn_2, 1, wx.FIXED_MINSIZE, 10)
        sizer.Add(self.btn_3, 1, wx.FIXED_MINSIZE, 10)
        sizer.Add(self.btn_close, 1, wx.FIXED_MINSIZE, 10)
         
        self.SetSizer(sizer) 

        self.btn_close.Bind(wx.EVT_BUTTON, self.parent.OnClose)
    
    def ShowStatus(self,event):
        self.parent.PanelToggle('status')

    def ShowNew(self,event):
        self.parent.PanelToggle('new')

########################################################################

"""
the main configuration screen
"""
class SettingsFrameNew(wx.Frame):
    def __init__(self, parent, id, title):
        self.parent = parent
        # Create form
        wx.Frame.__init__(self, parent, -1, title, size = (600, 400),
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.panel = {}
        self.panel['status'] = StatusPanel(self)
        self.panel['event'] = EventPanel(self)
        self.panel['profile'] = ProfilePanel(self)
        self.panel['nav'] = NavPanel(self)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.panel['nav'], 1, wx.FIXED_MINSIZE, 10)
        sizer.Add(self.panel['status'], 1, wx.FIXED_MINSIZE , 10)
        self.panel['status'].Show()
        self.panel['nav'].Show()

        self.SetSizerAndFit(sizer)

    def OnClose(self,event):
        self.Close(True)

    def PanelToggle(self,pname):
        for key in self.panels.keys():
            if key == pname:
                self.panel[key].Show()
            else:
                self.panel[key].Hide()

class SettingsFrame(wx.Frame):
    def __init__(self, parent, id, title):
        self.parent = parent
        # Create form
        wx.Frame.__init__(self, parent, -1, title, size = (600, 400),
        style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        
        # Control creation setup
        lbl_str= "Rainmaker Settings: " 

        # Create controls
        self.btn_close = wx.Button(self, id=wx.ID_ANY, label="Close")
        self.btn_start = wx.Button(self, id=wx.ID_ANY, label="Start")
        self.btn_stop = wx.Button(self, id=wx.ID_ANY, label="Stop")
        self.listbox = wx.ListBox(self, -1, (20, 20), (80, 120),[], wx.LB_SINGLE) 
        self.lbl_prf = wx.StaticText(self, -1, lbl_str , wx.Point(30, 30))
        self.lbl_status = wx.StaticText(self, -1, 'Status: ' , wx.Point(30, 30))
        
        # Basic control layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.lbl_prf, 1, wx.EXPAND | wx.ALL, 10)

        sizer_hv = wx.BoxSizer(wx.VERTICAL)
        sizer_hv.Add(self.btn_start, flag=wx.LEFT, border=10)
        sizer_hv.Add(self.btn_stop, flag=wx.LEFT, border=10)
        sizer_hv.Add(self.lbl_status, flag=wx.LEFT, border=10)
        
        sizer_h = wx.BoxSizer(wx.HORIZONTAL)
        sizer_h.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 10)
        sizer_h.Add(sizer_hv, 0, wx.EXPAND | wx.ALL, 10)

        sizer.Add(sizer_h, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.btn_close, flag=wx.RIGHT, border=10)        
        self.SetSizer(sizer)
         
        # Bind Events
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
        self.btn_start.Bind(wx.EVT_BUTTON, self.OnStart)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.OnStop)
        self.listbox.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListBoxClick) 
        
        # Other behavior
        self.btn_stop.Disable()
        self.PopulateListBox()

    def PopulateListBox(self):
        profiles = self.parent.user_configs.keys()
        started = []
        stopped = []
        for eh in self.parent.event_handlers:
            started.append(eh.uconf['name'])
            
        for label in profiles:
            if label not in started:
                stopped.append(label)
 
        self.listbox.SetItems(stopped)

    def OnListBoxClick(self,event):
        profile = event.GetText()
        started = []
        for eh in self.parent.event_handlers:
            started.append(eh.uconf['name'])
        if profle in started:
            self.btn_start.SetLabel('Stop')
        else:
            self.btn_start.SetLabel('Start') 
        
        
    def OnStart(self,event):
        idx = self.listbox.GetSelection()
        if not idx:
            return

        profile = self.listbox.GetString(idx)
        started = []
        for eh in self.parent.event_handlers:
            started.append(eh.uconf['name'])
        if profle in started:
            self.btn_start.SetLabel('Stop')
            self.parent.add_watch(profile)
            print "Started: "+ profile
        else:
            self.btn_start.SetLabel('Start') 
            self.parent.fsmonitor.remove_watch(profile)

        self.PopulateListBox()

    def OnStop(self,event):
        idx = self.listbox.GetSelection()
        if not idx:
            return
        profile = self.listbox.GetString(idx)
        self.parent.fsmonitor.remove_watch(profile)

    def OnClose(self,event):
        self.Close(True)

"""
the main portion of the application
-controls all other activity
"""
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
        prefs_form = SettingsFrameNew(self, -1, "rainmaker")
        prefs_form.Show(True)

    def DoTaskBar(self):
        print "MainAppFrame:DoConfig()"
        self.tbicon = TaskBarIcon(self)
        print self.config
        self.tbicon.LoadIcons(self.config['icons'])
        self.tbicon.Bind(wx.EVT_MENU, self.exitApp, id=wx.ID_EXIT)   
        self.Show(True)
        # display init icon
        self.tbicon.SetIconImage(90)

    def StartMonitor(self,profile):
        # Start Monitoring File System
        self.fsmonitor = Rainmaker(profile)
        self.config = self.fsmonitor.config
        self.user_configs = self.fsmonitor.user_configs
        self.event_handlers = self.fsmonitor.event_handlers

        #print "MainAppFrame:StartMonitor()"
        # display initial sync icon
        #self.tbicon.SetIconImage(91)
        
        #self.tbicon.SetIconImage(0)
        
        # Start Timer
        self.timer_poll = wx.Timer(self)
        self.timer_poll.Start(5000) # look every 5 seconds for events
        self.Bind(wx.EVT_TIMER, self.PollMonitor, self.timer_poll)
    
    def add_watch(self,profile):
        self.fsmonitor.add_watch(profile)
        self.tbicon.CreateMenu() 

    def PollMonitor(self, event):
        # Check FS monitor for changes
        result = self.fsmonitor.messages()
        if len(result) > 0:
            print result
        msg = self.config['icons'][98]['msg']
        self.tbicon.SetIconImage(98,msg)

    def exitApp(self,event):
        print "MainAppFrame:exitApp()"
        self.tbicon.RemoveIcon()  
        self.tbicon.Destroy()  
        self.fsmonitor.shutdown()
        sys.exit()

        
#---------------- run the program -----------------------  
def main(argv=None):
    profile = None
    if len(argv) > 1:
        profile = argv[1]

    print "main:wx.App()"
    app = wx.App(False)
    print "main:MainAppFrame()"
    frame = MainAppFrame(None, -1, ' ')
    print "main:StartMonitor()"
    frame.StartMonitor(profile)
    frame.DoTaskBar()
    print "main:frame.Show()"
    frame.Show(False)
    print "main:wx.MainLoop()"
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        app.exitApp()

if __name__ == '__main__':  
    main(sys.argv)
