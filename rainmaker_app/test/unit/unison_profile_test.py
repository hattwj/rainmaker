import unittest
import os

from rainmaker_app.app.profile import Profile
from rainmaker_app.conf import load
from rainmaker_app.lib import path
from rainmaker_app.tasks import install

class TestUnisonProfile(unittest.TestCase):

    def setUp(self):
        print 'Setup'
        unittest.TestCase.setUp(self)
        self.profile = Profile( load('profile/unison.yml') )
        self.user_dir=path.rel('tmp','.rainmaker')
        install(self.user_dir)
        self.profile.local_root = path.rel('tmp','sync1')
        self.profile.remote_root = path.rel('tmp','sync2')
        self.profile.backupdir = path.rel('tmp','backups')
    
    def tearDown(self):
        print 'Teardown'

    def test_io_funcs(self):
        self.assertFalse( self.profile.delete() )
        self.profile.path=os.path.join(self.user_dir,'profiles','test.yml')
        self.assertTrue( self.profile.save() )
        self.assertTrue( os.path.exists( self.profile.path ) )
        self.assertTrue( self.profile.delete() )
        self.assertFalse( os.path.exists( self.profile.path ) )
    
    # 
    def test_process_events(self):        
        self.profile.fs_monitor_init()
        self.add_events()
        commands = self.profile.process_events()
        self.assertEquals(len(commands),2)
        for cmd in commands:
            cmd_out = self.profile.run_cmd(cmd)
            out = self.profile.process_output(cmd_out)
            if 'normal' not in out:
                print cmd_out

            self.assertIn( 'normal',out)
            self.assertNotIn( 'fatal_error',out)
            if 'warning' in out:
                self.assertIn( 'first_run',out)
                
    # test cmd runner
    def test_cmd(self):
        a = self.profile.run_cmd('python %s/test/bin/stderr_stdout.py' % path.root)
        b = self.profile.run_cmd('unison /fraggle /rock -auto -batch')
        c = self.profile.run_cmd('unison fraggle rock -auto -batch')
    
    # test path validity 
    def test_paths(self):
        print self.profile.backupdir
        print self.profile.remote_events_dir

    def add_events(self):
        self.profile.fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.profile.local_root,'test.txg') ,
            is_dir = False
        )
        self.profile.fs_monitor.add_event(
            'created',
            src_path = os.path.join(self.profile.local_root,'test3.txt') ,
            is_dir = False
        )
        self.profile.fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.profile.local_root,'test.yml') ,
            dest_path = os.path.join(self.profile.local_root,'test2.yml') ,
            is_dir = False
        )
        self.profile.fs_monitor.add_event(
            'moved',
            src_path = os.path.join(self.profile.local_root,'test2.yml') ,
            dest_path = os.path.join(self.profile.local_root,'test3.yml') ,
            is_dir = False
        )

