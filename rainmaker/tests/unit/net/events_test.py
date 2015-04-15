from time import sleep
import warnings
from nose.tools import assert_raises

from rainmaker.net.events import Event, EventHandler, EventError, \
    Params

def test_event_get_should_raise_on_missing_key():
    event = Event('test', {})
    assert_raises(EventError, event.get, 'nosuchkey')
    assert {} == event.val()

def test_event_status_is_ok():
    e = Event('test', {})
    assert e.status == 'ok'

def test_fun_with_params_get_and_require():
    p = Params({'host': {'id':5, 'grr': 44}})
    assert {'id':5} == p.get('host').require('id').allow('test').val()
    assert {'id':5, 'grr':44} == p.get('host').require('id').allow('grr').val()
    assert_raises(EventError, p.get, 'nosuchkey')

def test_events_from_handler_should_reply():
    
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
    eh.trigger('Hi', reply=cmd_hi_reply)
    assert cmd_hi_reply.called == True
    assert cmd_hi.called == True

def test_missing_handler_should_warn():
    def cmd_na(event):
        pass
    eh = EventHandler(None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert eh.trigger('na') == False
    eh.register('na', cmd_na)
    assert eh.trigger('na') == True

def test_register_with_responds_to_decorator():
    eh = EventHandler() 
    @eh.responds_to('hi')
    def cmd_hi(event):
        event.reply('hello')
    def cmd_rhi(event):
        cmd_rhi.ran = True
    cmd_rhi.ran = False
    eh.trigger('hi', reply=cmd_rhi)
    assert cmd_rhi.ran == True

