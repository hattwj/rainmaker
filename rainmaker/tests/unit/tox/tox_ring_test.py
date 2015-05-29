from nose.tools import assert_raises
from pytox import OperationFailedError
from rainmaker.tests import test_helper
from rainmaker.tox.tox_ring import ToxBase, ToxBot, acts_as_message_bot, \
        acts_as_connect_bot, acts_as_search_bot
from rainmaker.tests import factory_helper as fh

def test_toxbot_multiple_inheritance_is_good():
    
    tox = ToxBot(fh.Sync())
    assert_raises(OperationFailedError, tox.send_message, 1, 'hi')
    gg = tox.group_message_send(1, 'hi')
    # weird, why must we print the result?
    # - does not raise error unless we print
    assert_raises(OperationFailedError, print, gg)
    assert_raises(NotImplementedError, tox.send, 'hi')
    assert_raises(NotImplementedError, tox.send, 1, 'hi', fid=1)

def test_base_tox_interface_has_blank_methods():
    tox = ToxBase(fh.Sync(fake=True))
    assert_raises(NotImplementedError, tox.send, 'hi')
    assert_raises(NotImplementedError, tox.send, 1, 'hi', fid=1)

class MockTox(ToxBase):
    ''' Mock '''
    def __init__(self, sync=None, data=None):
        super().__init__(sync, data=data)
        self._g_msgs = []
        self._f_msgs = []
        self._links = {}

    def group_message_send(self, gid, msg):
        self._g_msgs.append([gid, msg])
        for gid, fid, tox in self._links.get('gid%s' % gid, []):
            tox.on_group_message(gid, fid, msg)
        
    def send_message(self, fid, msg):
        self._f_msgs.append([fid, msg])
        for gid, fid, tox in self._links.get('fid%s' % fid, []):
            tox.on_friend_message(fid, msg)
    
    # mock a connection for messages
    def _mock_link(self, tox, gid, fid, recurse=True):
        dict_append(self._links, 'gid%s' % gid, [gid, fid, tox])
        dict_append(self._links, 'fid%s' % fid, [gid, fid, tox])
        if recurse:
            tox._mock_link(self, gid, fid, recurse=False)
    
    def get_keys(self):
        return ('123456789','987654321')

    def get_address(self):
        return '123456789'
def dict_append(adict, key, val):
    arr = adict.get(key, [])
    arr.append(val)
    adict[key] = arr

def test_acts_as_message_bot_can_send_large_msgs():
    tox = MockTox(fh.Sync(fake=True))
    gmsgs = tox._g_msgs
    fmsgs = tox._f_msgs
    acts_as_message_bot(tox)
    tox.send('hi', {'a', 'b'*1500})
    assert len(gmsgs) == 2
    assert len(gmsgs[0][1]) == 1300
    assert len(gmsgs[1][1]) < 300
    tox.send('hi', {'a', 'b'*1500}, fid=4)
    assert len(fmsgs) == 2
    assert len(fmsgs[0][1]) == 1300
    assert len(fmsgs[1][1]) < 300

def test_event_messages_and_replies_should_pass_through_transport():
    def cmd_test(event):
        cmd_test.ran = True
        event.reply('wow!', {'hi': 55})
        assert event.val() == {'kibble':'wibble', 'gid': None, 'fid':1}
    def cmd_rtest(event):
        cmd_rtest.ran = True
        assert event.status == 'wow!'
        assert event.val() == {'hi': 55, 'gid':None, 'fid':1}
    cmd_test.ran = False
    cmd_rtest.ran = False
    t1 = MockTox(fh.Sync(fake=True))
    t2 = MockTox(fh.Sync(fake=True))
    t2.register('hello_world', cmd_test)
    acts_as_message_bot(t1)
    acts_as_message_bot(t2)
    t1._mock_link(t2, 1, 1)
    t1.send('hello_world', {'kibble':'wibble'}, fid=1, reply=cmd_rtest)
    assert cmd_test.ran
    assert cmd_rtest.ran

