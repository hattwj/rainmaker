from nose.tools import assert_raises
from pytox import OperationFailedError
from rainmaker.tests import test_helper
from rainmaker.tox.tox_ring import ToxBase, ToxBot, acts_as_message_bot, \
        acts_as_connect_bot, acts_as_search_bot

def test_toxbot_multiple_inheritance():
    tox = ToxBot()
    assert_raises(OperationFailedError, tox.send_message, 1, 'hi')
    gg = tox.group_message_send(1, 'hi')
    # weird, why must we print the result?
    assert_raises(OperationFailedError, print, gg)
    assert_raises(NotImplementedError, tox.gsend, 'hi')
    assert_raises(NotImplementedError, tox.fsend, 1, 'hi')

def test_base_interface():
    tox = ToxBase()
    assert_raises(NotImplementedError, tox.gsend, 'hi')
    assert_raises(NotImplementedError, tox.fsend, 1, 'hi')

class MockTox(ToxBase):
    ''' Mock '''
    def __init__(self, data=None):
        super().__init__(data)
        self._g_msgs = []
        self._f_msgs = []

    def group_message_send(self, gid, msg):
        self._g_msgs.append([gid, msg])

    def send_message(self, fid, msg):
        self._f_msgs.append([fid, msg])

def test_acts_as_message_bot():
    tox = MockTox()
    gmsgs = tox._g_msgs
    fmsgs = tox._f_msgs
    acts_as_message_bot(tox)
    tox.gsend('hi', {'a', 'b'*1500})
    assert len(gmsgs) == 2
    assert len(gmsgs[0][1]) > 1300
    assert len(gmsgs[0][1]) < 1330
    tox.fsend(4, 'hi', {'a', 'b'*1500})
    assert len(fmsgs) == 2
    assert len(fmsgs[0][1]) > 1300
    assert len(fmsgs[0][1]) < 1330

def test_message_callback():
    def cmd_test(event):
        cmd_test.ran = True
    def cmd_rtest(event):
        cmd_rtest.ran = True
    tox = MockTox()
    gmsgs = tox._g_msgs
    fmsgs = tox._f_msgs
    acts_as_message_bot(tox)
    tox.register('test', cmd_test)

