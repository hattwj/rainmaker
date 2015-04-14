from time import sleep

from nose.tools import assert_raises
from rainmaker.net.utils import LStore

def test_lstore_times_out():
    fb = LStore(0.2)
    key = fb.append(5)
    assert fb.get(key) == 5
    key = fb.append(5)
    sleep(0.25)
    assert_raises(KeyError, lambda: fb[key])

def test_lstore_refreshes_timer_on_get():
    fb = LStore(0.25)
    key = fb.append(5)
    sleep(0.1)
    fb[key]
    sleep(0.2)
    assert fb.get(key) == 5

def test_lstore_can_pop():
    fb = LStore(0.2)
    fb[''] = 5
    fb.pop('')
    assert fb.pop('') == None
    
def test_lstore_can_put():
    fb = LStore(0.2)
    fb.put('', 5)
    assert fb[''] == 5

def test_lstore_can_append():
    fb = LStore(0.2)
    key = fb.append(5)
    assert fb[key] == 5

def test_lstore_can_provide_default_yield():
    def _gen():
        _gen.ran = True
        return 5
    _gen.ran = False
    fb = LStore()
    for v in fb.yget('', _gen):
        assert v == 5
    assert _gen.ran == True

