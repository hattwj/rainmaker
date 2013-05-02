import unittest
import os


from rainmaker_app.app.profile import FsMonitor
from rainmaker_app.lib.path import rel
from rainmaker_app.tasks import install

class TestFsMonitor(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.fs_monitor = FsMonitor()
        self.path = rel('tmp','sync1')

    def test_ignore_yml(self):
        ignore_fs_monitor = FsMonitor(ignore_patterns = ['*.yml']) 
        self.add_events(ignore_fs_monitor)
        events = ignore_fs_monitor.get_events(self.path)
        self.assertEquals(len(events),3)

    def test_get_events(self):
        src_path=os.path.join(self.path,'test.yml')

    def add_events(self,fs_monitor):        
        fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.path,'test.yml') ,
            dest_path = os.path.join(self.path,'test2.baml') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.path,'test.yml') ,
            dest_path = os.path.join(self.path,'test2.txt') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.path,'test.yml') ,
            is_dir = False
        )
        fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.path,'test.yml2') ,
            is_dir = False
        )
