import unittest
import os


from rainmaker_app.app.profile import FsMonitor
from rainmaker_app.lib.path import rel
from rainmaker_app.tasks import install

from rainmaker_app.test import test_helper

class TestFsMonitor(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        test_helper.clean(['sync1'])
        watch_path = os.path.join(test_helper.temp_dir,'sync1')
        log_path=os.path.join(test_helper.user_dir,'fsmon.log')
        self.fs_monitor = FsMonitor(watch_path,log_path)
        self.watch_path=watch_path
        self.log_path = log_path

    def test_ignore_yml(self):
        ignore_fs_monitor = FsMonitor(self.watch_path,self.log_path,ignore_patterns = ['*.yml']) 
        self.add_events(ignore_fs_monitor)
        events = ignore_fs_monitor.get_events()
        self.assertEquals(len(events),3)

    def test_get_events(self):
        src_path=os.path.join(self.watch_path,'test.yml')

    def add_events(self,fs_monitor):        
        fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.watch_path,'test.yml') ,
            dest_path = os.path.join(self.watch_path,'test2.baml') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.watch_path,'test.yml') ,
            dest_path = os.path.join(self.watch_path,'test2.txt') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.watch_path,'test.yml') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.watch_path,'test.yml2') ,
            is_dir = False
        )
