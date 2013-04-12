import unittest
from rainmaker_app.app.model import UnisonProfile

class TestProfile(unittest.TestCase):

    def setUp(self):
        pass
   
    def test_address(self):
        profile = UnisonProfile()
        self.assertIsNotNone(profile.address)
        profile.address = 'gggggg'
    
    def test_save_func(self):
        profile = UnisonProfile()
        profile.path='test.yml'
        print profile.path
        profile.save()

