import unittest
import os


from rainmaker_app.app.model import BaseHandler
from rainmaker_app.lib.path import rel
from rainmaker_app.lib.tasks import install

class TestBaseHandler(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.handler = BaseHandler()
        self.path = rel('tmp','sync1')

    def test_ignore_yml(self):
        ignore_handler = BaseHandler(ignore_patterns = ['*.yml']) 
        self.add_events(ignore_handler)
        events = ignore_handler.get_events(self.path)
        self.assertEquals(len(events),3)

    def test_get_events(self):
        src_path=os.path.join(self.path,'test.yml')

    def add_events(self,handler):        
        handler.add_event(
            'moved',
            src_path = os.path.join(self.path,'test.yml') ,
            dest_path = os.path.join(self.path,'test2.baml') ,
            is_dir = False
        )
        handler.add_event(
            'moved',
            src_path = os.path.join(self.path,'test.yml') ,
            dest_path = os.path.join(self.path,'test2.txt') ,
            is_dir = False
        )
        handler.add_event(
            'created',
            src_path = os.path.join(self.path,'test.yml') ,
            is_dir = False
        )
        handler.add_event(
            'created',
            src_path = os.path.join(self.path,'test.yml2') ,
            is_dir = False
        )
