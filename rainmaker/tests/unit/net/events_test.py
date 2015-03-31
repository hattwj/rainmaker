from time import sleep

from nose.tools import assert_raises

from rainmaker.net.events import FuncBuffer, Event, EventHandler, EventError, \
    Params

def test_event_should_raise_on_missing_get():
    event = Event('test', {})
    assert_raises(EventError, event.get, 'nosuchkey')
    assert {} == event.val()

def test_fun_with_params():
    p = Params({'host': {'id':5, 'grr': 44}})
    assert {'id':5} == p.get('host').require('id').allow('test').val()
    assert {'id':5, 'grr':44} == p.get('host').require('id').allow('grr').val()
    assert_raises(EventError, p.get, 'nosuchkey')


def test_func_buffer():
    fb = FuncBuffer()
    key = fb.add(5)
    assert fb.get(key) == [5]
    key = fb.add(5, timeout=0.2)
    sleep(0.25)
    assert_raises(KeyError, fb.get, key)

def test_event_handler():
    def cmd_hi(event):
        cmd_hi.called = True
        event.reply('Hello')

    def cmd_hi_reply(event):
        cmd_hi_reply.called = True
        assert event.status == 'Hello'
    
    cmd_hi_reply.called = False
    cmd_hi.called = False
    eh = EventHandler(None)
    eh.register('Hi', cmd_hi)
    eh.call_event('Hi', reply=cmd_hi_reply)
    assert cmd_hi_reply.called == True
    assert cmd_hi.called == True

def test_missing_handler():
    def cmd_na(event):
        pass
    eh = EventHandler(None)
    assert eh.call_event('na') == False
    eh.register('na', cmd_na)
    assert eh.call_event('na') == True

