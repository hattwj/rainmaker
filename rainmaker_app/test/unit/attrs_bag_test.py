import unittest
from rainmaker_app.lib import AttrsBag 
from rainmaker_app.test.fixtures import attrs_bag_data

class TestAttrsBag(unittest.TestCase):

    def setUp(self):
        print 'Setup: %s' % self.__class__.__name__
        unittest.TestCase.setUp(self)

        self.bag = AttrsBag()
    def tearDown(self):
        print 'Teardown: %s' % self.__class__.__name__

    def test_parse(self):
        pass
