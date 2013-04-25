import unittest
import os
import shutil

from rainmaker_app.app.profile import LogMonitor
from rainmaker_app.lib.path import rel

class TestLogMonitor(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.log_files=[]
        self.path = rel('tmp','log_monitor')
        try:
            os.mkdir(self.path)
        except:
            pass
        self.monitor = LogMonitor(self.path)
    
    def tearDown(self):
        for p in self.log_files:
            os.remove(p)
        
    def test_get_events(self):
        ''' test ability to find new events '''
        self.assertEquals( len(self.monitor.get_events()),0)
        
        self.copy('10_valid_events.log')
        self.assertEquals( len(self.monitor.get_events()),10)
        
        self.copy('10_valid_events.log')
        self.assertEquals( len(self.monitor.get_events()),0)

    def copy(self,p,pp=None):
        pp= p if not pp else pp
        src_path = rel('test','fixtures',p)
        dest_path = rel('tmp','log_monitor',pp)
        if dest_path not in self.log_files:
            self.log_files.append(dest_path)
        shutil.copy(
            src_path,dest_path
        )

