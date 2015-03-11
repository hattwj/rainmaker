from nose.tools import assert_raises

from rainmaker.tests import test_helper
from rainmaker.tox.tox_ring import Event, Params, EventError

## SyncBot
# it should be able to send and receive 
# - fs_events
# - hosts
# - transfer file parts
# - Authorization
#
# connection / state
#

def test_event_should_raise_on_missing_get():
    event = Event('test')
    assert_raises(EventError, event.get, 'nosuchkey')
    assert {} == event.val()

def test_fun_with_params():
    p = Params(host={'id':5, 'grr': 44})
    assert {'id':5} == p.get('host').require('id').allow('test').val()
    assert {'id':5, 'grr':44} == p.get('host').require('id').allow('grr').val()
    assert_raises(EventError, p.get, 'nosuchkey')

