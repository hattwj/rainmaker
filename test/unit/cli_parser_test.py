import unittest
import os

from app.initialize import CliParser

class TestCliParser(unittest.TestCase):

    def setUp(self):
        print 'Setup: %s' % self.__class__.__name__
        unittest.TestCase.setUp(self)
        self.parser = CliParser()

    def tearDown(self):
        print 'Teardown: %s' % self.__class__.__name__

    def test_parse(self):
        print self.parser.parse(['create'])
        print self.parser.parse(['-h'])
