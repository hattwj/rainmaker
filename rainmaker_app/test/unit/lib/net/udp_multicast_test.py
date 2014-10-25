from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

from rainmaker_app.lib.net import udp_multicast

# stub out module import
fake_host = '127.0.0.1'
def get_fakeaddress(addr=None):
    return fake_host
udp_multicast.get_address = get_fakeaddress
from rainmaker_app.lib.net.udp_multicast import *


##############################
# Fake objects for testing
##############################

class FakeTransport(object):
    def __init__(self):
        self._msgs = []
    def write(self, msg, addr_port):
        self._msgs.append( [msg, addr_port] )
    def clear(self):
        self._msgs = []

    @property
    def msgs(self):
        ''' messages sent by server '''
        return self._msgs

    def getHost(self):
        return FakeHostInfo()

    def joinGroup(self, *args):
        pass

class FakeDHT(object):
    pass

class FakeClientFactory(object):
    _host = None

    def dht_client(self, host):
        self._host = host

import operator
class FakeReactor(object):
    def __init__(self):
        self.restart()

    def restart(self):
        self._deferreds = []

    def callLater(self, interval, func, *params):
        tstamp = (1000*interval) + time_now()
        self._deferreds.append([tstamp, func, params])

    def run_deferreds(self):
        add_again = []
        # sort by interval
        self._deferreds = sorted(self._deferreds, key=operator.itemgetter(0))
        print self._deferreds

        while len(self._deferreds)>0:
            func_info = self._deferreds.pop()
            tstamp, func, params = func_info
            if time_now() > tstamp:
                func(*params)
            else:
                add_again.append(func_info)
        self._deferreds = add_again

port = 444
local = (fake_host, port,) 
remote = ('192.168.0.2', port,) 
remote2 = ('192.168.0.3', port,) 
fake_transport = FakeTransport()
fake_dht = FakeDHT()
app.reactor = FakeReactor()

class FakeHostInfo(object):
    host = local
    port = port

def run_fake_deferreds():
    app.reactor.run_deferreds()

##########
# start tests

class RequestEncoderTest(unittest.TestCase):

    def setUp(self):
        RequestEncoder.buffer_wipe()
        time_elapsed(reset=True)

    def test_encoder_does_encode_singles(self):
        request = RequestEncoder(local, 'ping')
        msgs = [msg for msg in request.iter_messages()]
        self.assertEquals(len(msgs), 1)
        self.assertEquals('ping' in msgs[0], True)
    
    def test_encoder_does_encode_multi(self):
        data = '123456789'* 1000
        request = RequestEncoder(local, 'store_value', data)
        msgs = [msg for msg in request.iter_messages()]
        self.assertEquals(len(msgs) > 1, True)
        self.assertEquals('store_value' in msgs[0], True)
        
    def test_buffer_does_store_messages(self):
        data = '0123456789'* 1000
        request = RequestEncoder(local, 'store_value', data)
        for msg in request.iter_messages(3, 3):
            pass
        new = RequestEncoder.find(request.fid)
        self.assertEquals(new, request)

    def test_buffer_does_expire(self):
        data = '0123456789'* 1000
        request = RequestEncoder(local, 'store_value', data)
        for msg in request.iter_messages(3, 3):
            pass
        time_elapsed(request.msg_ttl*1000)
        run_fake_deferreds()
        new = RequestEncoder.find(request.fid)
        self.assertEquals(new, None)
        
    
    def test_encoder_can_iterate_subset(self):
        data = '0123456789'* 1000
        RequestEncoder.mtu = 101
        request = RequestEncoder(local, 'store_value', data)
        count = 0
        for msg in request.iter_messages(3, 3):
            count += 1
        self.assertEquals(count == 3, True)
    
    def test_encoder_limited_by_mtu(self):
        data = '0123456789'* 1000
        RequestEncoder.mtu = 501
        request = RequestEncoder(local, 'store_value', data)
        count = 0
        for msg in request.iter_messages():
            self.assertEquals(len(msg) <= request.mtu, True)
            #print [count, request.fmax]
            count += 1
        self.assertEquals(count == request.fmax+1, True)

class BaseResponderTest(unittest.TestCase):
    
    def test_responder_knows_its_name(self):
        res = BaseResponder()
        self.assertEquals(res.name, 'base')

class PingResponderTest(BaseResponderTest):
    
    def test_responder_knows_its_name(self):
        res = PingResponder()
        self.assertEquals(res.name, 'ping')

class RequestParserTest(unittest.TestCase):
    
    # Test Preparation
    def setUp(self):
        RequestParser.buffer_wipe()
        RequestParser.transport = FakeTransport()
        RequestParser.dht = FakeDHT()
        time_elapsed(reset=True)

    def test_parser_finds_request_details(self): 
        msg = 'rain%s%s' % (version, 'store_host5678:0:4:snapple')
        request = RequestParser(local, msg)
        self.assertEquals(request.error, request.ERR_NONE)
        self.assertEquals(request.action, 'store_host')
        self.assertEquals(request.fid, 5678)
        self.assertEquals(request.fno, 0)
        self.assertEquals(request.fmax, 4)
        self.assertEquals(request.data, 'snapple')

    def test_parser_limits_fno_to_fmax(self):
        msg = 'rain%s%s' % (version, 'store_host5655:1:0:snapple')
        request = RequestParser(local, msg)
        self.assertEquals(request.error, request.ERR_FRAME)

    def test_parser_finds_responder(self):
        # finds responder
        msg = 'rain%s%s' % (version, 'ping')
        request = RequestParser(local, msg)
        self.assertEquals(request.error, request.ERR_NONE)
        self.assertEquals(request.action, 'ping')
        self.assertEquals(request.responder.name, 'ping')
    
    def test_parser_detects_multipart(self):
        # detect not multipart
        msg = 'rain%s%s' % (version, 'ping')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_multipart, False)
        # detect multipart
        msg = 'rain%s%s' % (version, 'store_host5655:0:1:snapple')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_multipart, True) 
    
    def test_parser_detects_multipart_incomplete(self):
        msg = 'rain%s%s' % (version, 'store_host88:0:1:snapple')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_INCOMPLETE)
        msg = 'rain%s%s' % (version, 'store_host88:1:1:snapple')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_NONE)

    def test_multipart_runs_if_complete(self):
        # incomplete requests won't run
        msg = 'rain%s%s' % (version, 'store_host5655:0:1:Hello')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, False)
        # completed requests do run
        msg = 'rain%s%s' % (version, 'store_host5655:1:1:World')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, True) 
        self.assertEquals(request.params,'HelloWorld')
    
    def test_buffer_insert_respects_fno(self):
        # request arrival order shouldn't matter
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, True)
        self.assertEquals(request.params,'WorldHello')
        
    def test_requests_run_when_complete(self): 
        # requests should run once only 
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, False)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, True)
    
    def test_requests_run_only_once(self): 
        # requests should run once only 
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, False)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, True)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:Hello')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.is_ready_to_run, False)
    
    def test_requests_can_expire(self):
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        time_elapsed(request.buffer_ttl*1001)
        run_fake_deferreds()
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_INCOMPLETE)
        self.assertEquals(request.is_ready_to_run, False)


    def test_buffer_refractory_period_exists(self):
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:1:1:New')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:Command')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_BUFFER)
    
    def test_buffer_refractory_period_ends(self):
        msg = 'rain%s%s' % (version, 'store_host565:1:1:Hello')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:World')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:1:1:New')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:Command')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_BUFFER)
        run_fake_deferreds()        
        msg = 'rain%s%s' % (version, 'store_host565:1:1:New')
        request = RequestParser.parse(local, msg)
        msg = 'rain%s%s' % (version, 'store_host565:0:1:Command')
        request = RequestParser.parse(local, msg)
        self.assertEquals(request.error, request.ERR_NONE)

class MulticastServerUDPTest(unittest.TestCase):
    
    # Test Preparation
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        self.data = load('test/fixtures/unit/lib/net/udp_multicast_test.yml')
        yield load_fixture( 'setup', self.data )
        yield load_fixture( self._testMethodName, self.data )
        self.protocol = MulticastServerUDP(8000, listen_port=port)
        self.transport = FakeTransport()
        self.protocol.transport = self.transport
        self.protocol.startProtocol()

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()
    
    # Tests
    def test_announce_command(self):
        ''' test ability to receive and process announce command '''
        # aliases
        p = self.protocol
        t = self.transport 
        
        p.client_factory = FakeClientFactory()

        # announce host
        msg = DatagramParser.encode('announce', tcp_port=8000)
        err = p.datagramReceived(msg, remote2)
        self.assertEquals(err, p.ERR_NONE)
        
        # check for response
        host = p.client_factory._host
        self.assertEquals(host==None, False)
        self.assertEquals(host.tcp_port, 8000)
        self.assertEquals(host.address, remote2[0])
    #TODO: Add tests

