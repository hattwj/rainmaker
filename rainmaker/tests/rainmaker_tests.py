from nose.tools import *
from rainmaker.tests import test_helper

def setup():
    print("Base SETUP!")

def teardown():
    print("Base TEAR DOWN!")
    test_helper.clean_temp_dir()

def test_basic():
    print("I RAN!")
