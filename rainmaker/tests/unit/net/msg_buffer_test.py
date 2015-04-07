from time import sleep
from rainmaker.net import msg_buffer

def test_buffer_send_in_chunks():
    data = 'Test'*1000
    mbuf = msg_buffer.MsgBuffer(chunk=1000)
    for mno, mto, msg in mbuf.send('345', 'cmd', 'ok', data):
        assert len(msg) <= 1000
    assert mno == 4 # 5 msgs


