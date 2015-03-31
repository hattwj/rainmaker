from time import sleep
from rainmaker.net import msg_buffer

def test_buffer_works():
    mbuf = msg_buffer.MessageBuffer('first', 0)
    result = mbuf.add(0, 'Test')
    assert result == 'Test'

    mbuf = msg_buffer.MessageBuffer('first', 10)
    for x in range(0, 10):
        result = mbuf.add(x, 'Test')
        assert result == None
    assert mbuf.add(10, 'Test') == 'Test' * 11 

def test_buffer_times_out():
    mbuf = msg_buffer.MessageBuffer('first', 1, timeout=0.2)
    mbuf = msg_buffer.MessageBuffer.find('first')
    assert mbuf is not None
    sleep(0.25)
    mbuf = msg_buffer.MessageBuffer.find('first')
    assert mbuf is None 

def test_string_buffer():
    data = 'Test'*1000
    counter = 0
    for count, total, dat in msg_buffer.string_buffer(data, chunk=1000):
        counter += 1
        assert len(dat) == 1000
    assert counter == 4

def test_send_buffer():
    for m in msg_buffer.send_buffer('ping'):
        assert m == "ping:1:1\n"

def test_send_recv_buffer():
    data = {'a':[None]*3}
    result = 999
    for m in msg_buffer.send_buffer('ping', data, chunk=5):
        for cmd, r in msg_buffer.recv_buffer(1, m):
            assert r == data
