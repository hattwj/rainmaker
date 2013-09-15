import unittest
import os

print 'DEBUG'
import sys

from rainmaker_app.app.initialize import AppLoop
from rainmaker_app.app.profile import ProfileManager, Profile
from rainmaker_app.test import test_helper

class TestProfileManager(unittest.TestCase):

    def setUp(self):
        print 'Setup'
        unittest.TestCase.setUp(self)
        test_helper.clean(['sync1','sync2'])
        loop=AppLoop(test_helper.events_dir)
        self.loop = loop
        self.runner = self.create_pm('sync1')
    
    def create_pm(self,title):
        ''' Create ProfileManager obj'''
        vals = test_helper.load('test/fixtures/%s.yml' % title)
        base = test_helper.load('conf/profile/unison.yml')
        profile = Profile(base,vals)
        profile.user_dir = test_helper.user_dir                 
        runner = self.loop.start_profile(profile)
        return runner

    def tearDown(self):
        print 'Teardown'
        self.loop.shutdown()
        test_helper.clean(['sync1','sync2'],create=False)

    def test_monitoring(self):
        ''' Test local and remote fs monitoring'''
        # update log file and ignore events
        self.runner.startup()
        
        # update single file
        src_file_rel = 'file.txt'
        rand_file(self.runner.profile,src_file_rel)

        # Find change in 1 local file
        events = self.runner.get_events(all_events=True)
        cmds = self.runner.events_to_cmds(events)
        self.assertEquals(len(cmds),1)
        self.assertEquals(events[0]['event_src_path_rel'],src_file_rel)
    
    def test_server_side_sync(self):
        self.runner.startup()
        
        # create 2nd profile manager
        pm2=self.create_pm('sync2')        
        pm2.startup()
        
        # change remote file
        rand_file(pm2.profile ,'rand2')
        
        # send change to remote events log
        sync(pm2)
        
        # sync with remote logs and
        # find a change in 1 remote file
        events = self.runner.get_events(all_events=True)
        cmds = self.runner.events_to_cmds(events)
        self.assertEquals(len(cmds),1)

    def test_process_events(self):
        self.runner.startup()
        rand_file(self.runner.profile,'a')
        rand_file(self.runner.profile,'b')
        events = self.runner.get_events()
        commands = self.runner.events_to_cmds(events)
        print events
        #self.assertEquals(len(events),4)
        self.assertEquals(len(commands),1)
        for cmd in commands:
            cmd_out = self.runner.run_cmd(cmd)
            out = cmd_out['output']
            if 'change' not in out:
                print cmd_out

            self.assertIn( 'change',out)
            self.assertNotIn( 'fatal_error',out)
            if 'warning' in out:
                self.assertIn( 'first_run',out)                
    
    def test_empty_dirs(self):
        ''' Test detection of empty dirs '''
        self.runner.startup()

        path1 = os.path.join(test_helper.temp_dir,'sync1','froms1')
        epath1 = os.path.join(test_helper.temp_dir,'sync2','froms1')
        
        path2 = os.path.join(test_helper.temp_dir,'sync2','froms2')
        epath2 = os.path.join(test_helper.temp_dir,'sync1','froms2')
        
        test_helper.fs.mkdir(path1)
        test_helper.fs.mkdir(path2)
        sync(self.runner)

        self.assertTrue( os.path.exists(epath1) )
        self.runner.run_cmd(key='startup')
        self.assertTrue( os.path.exists(epath2) )
    
    def test_notifications(self):
        ''' Test desktop notifications '''
        self.runner.startup()

        # create 2nd profile manager
        pm2=self.create_pm('sync2')        
        pm2.startup()
        
        # change remote file
        rand_file(pm2.profile ,'rand2')
        
        # send change to remote events log
        sync(pm2)
        
        # sync with remote logs and
        # find a change in 1 remote file
        events = self.runner.get_events(all_events=True)
        cmds = self.runner.events_to_cmds(events)

        self.runner.notify(events)
        


def sync(runner):
    events = runner.get_events(all_events=True)
    cmds = runner.events_to_cmds(events)
    for cmd in cmds:
        runner.run_cmd(cmd)
        
def rand_file(profile,path):
    rand_str = profile.subst('${rand:1000}')  
    f=open(os.path.join(profile.subst(profile.local_root),path),'w')
    f.write(rand_str)
    f.close()
    return rand_str 
