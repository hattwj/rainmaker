import unittest
import os

from lib import RecordHooks
from lib import path

class TestRecordHooks(unittest.TestCase):

    def setUp(self):
        print 'Setup'
        unittest.TestCase.setUp(self)
        self.rh = RecordHooks()

    def tearDown(self):
        print 'Teardown'

    def test_sompin(self):
        print 'RecordHooks needs test coverage'
