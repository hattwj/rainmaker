from time import sleep
from rainmaker.net import msg_buffer

def test_buffer_send_in_chunks():
    data = 'Test'*1000
    mbuf = msg_buffer.MsgBuffer(chunk=1000)
    mno = 0
    for msg in mbuf.send('345', 'cmd', 'ok', data):
        assert len(msg) <= 1000
        mno += 1
    assert mno == 5 # 5 msgs


