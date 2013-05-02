import unittest
import os

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

        # Look for new events
        events = self.runner.get_events(all_events=True)
        cmds = self.runner.events_to_cmds(events)
        print events
        self.assertEquals(len(cmds),1)
        self.assertEquals(events[0]['event_src_path_rel'],src_file_rel)
       
        # sync empty dir?

        
def rand_file(profile,path):
    rand_str = profile.subst('${rand:1000}')  
    f=open(os.path.join(profile.subst(profile.local_root),path),'w')
    f.write(rand_str)
    f.close()
    return rand_str 
