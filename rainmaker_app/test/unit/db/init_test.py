import unittest
import os

from rainmaker_app.db.init import initDB 
from rainmaker_app.test import test_helper

class TestInit(unittest.TestCase):

    def setUp(self):
        print 'Setup: %s' % self.__class__.__name__
        self.location = os.path.join(test_helper.user_dir,'test.sqlite')
    def tearDown(self):
        print 'Teardown: %s' % self.__class__.__name__

    def testInitDB(self):
        initDB(self.location)
