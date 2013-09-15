import unittest
from rainmaker_app.app.profile import Profile
from rainmaker_app.lib.conf import load
class TestProfile(unittest.TestCase):

    def setUp(self):
        pass
   
    def test_address(self):
        profile = Profile(load('profile/base.yml'))
        self.assertIsNotNone(profile.address)
        profile.address = 'gggggg'
    
    def test_save_func(self):
        pass
        #profile = Profile()
        #profile.path='test.yml'
        #print profile.path
        #profile.save()

