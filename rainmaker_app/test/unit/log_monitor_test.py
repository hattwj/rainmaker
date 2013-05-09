import unittest
import os
import shutil

from rainmaker_app.test import test_helper
from rainmaker_app.app.profile import LogMonitor
from rainmaker_app.lib.path import rel

class TestLogMonitor(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.log_files=[]
        test_helper.clean()
        self.path = test_helper.events_dir
        self.log_mon = LogMonitor(self.path,'*.log')

    
    def tearDown(self):
        pass

    def test_get_events(self):
        ''' test ability to find new events '''
        self.assertEquals( len(self.log_mon.get_events()),0)
        
        self.copy('10_valid_events.log')
        self.assertEquals( len(self.log_mon.get_events()),10)
        
        self.copy('10_valid_events.log')
        self.assertEquals( len(self.log_mon.get_events()),0)

    def copy(self,p,pp=None):
        pp= p if not pp else pp
        src_path = os.path.join(test_helper.fixtures_dir,p)
        dest_path = os.path.join(test_helper.events_dir,pp)
        test_helper.fs.copy(
            src_path,dest_path
        )
        self.log_mon.scan_files()

