from time import sleep

from nose.tools import assert_raises
from rainmaker.net.utils import LStore

def test_buffer_times_out():
    fb = LStore(0.2)
    key = fb.append(5)
    assert fb.get(key) == 5
    key = fb.append(5)
    sleep(0.25)
    assert_raises(KeyError, lambda: fb[key])

def test_buffer_refreshes():
    fb = LStore(0.25)
    key = fb.append(5)
    sleep(0.1)
    fb[key]
    sleep(0.2)
    assert fb.get(key) == 5

