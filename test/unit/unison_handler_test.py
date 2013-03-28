import unittest
import os

from app.model import UnisonProfile
from app.model import UnisonHandler

from lib import path
from lib.tasks import install

class TestUnisonHandler(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.profile = UnisonProfile()
        self.handler = UnisonHandler()
        self.path = path.rel('tmp','sync1')
        self.profile.local_root = self.path
        self.handler.attrs = dict( 
            self.profile.attrs_dump('default').items() +
            self.profile.attrs_dump().items()
        )

    def test_build_command(self):
        src_path=os.path.join(self.path,'test.yml')
        self.handler.add_event(
            'created',
            src_path=src_path,
            is_dir=True)
        events = self.handler.get_events()
        cmds = self.handler.build_cmds(events)
        print cmds

    def test_template(self):
        from string import Template
        gg = Template('yabble ${flag} dabble')
        print gg.safe_substitute({
            'flag':'quack'
        })
