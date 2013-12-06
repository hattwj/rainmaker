#!/usr/bin/env python
from twisted.python import log
from twisted.protocols import amp
from twisted.internet import reactor, defer, ssl
from rainmaker_app.lib.net.start_tls import ClientFactory, ServerFactory, FilesResource
from rainmaker_app.test.test_helper import *
from rainmaker_app.test.db_helper import *

c = '''-----BEGIN CERTIFICATE-----
MIIBnTCCAUcCAgPoMA0GCSqGSIb3DQEBCwUAMFkxCzAJBgNVBAYTAnVzMQ0wCwYD
VQQIEwRoZXJlMQ4wDAYDVQQHEwV0aGVyZTENMAsGA1UEChMEdGhlbTEMMAoGA1UE
CxMDYW5kMQ4wDAYDVQQDEwVzdHVmZjAeFw0xMzExMjcwMjI3MjJaFw0yMzExMjUw
MjI3MjJaMFkxCzAJBgNVBAYTAnVzMQ0wCwYDVQQIEwRoZXJlMQ4wDAYDVQQHEwV0
aGVyZTENMAsGA1UEChMEdGhlbTEMMAoGA1UECxMDYW5kMQ4wDAYDVQQDEwVzdHVm
ZjBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQCxQF1VdCR+TD34WRDBjW9RAoV79NR/
8XbhIBdeBUbtyJtf6L0lcX1+uXFOzHNTVv0no3Z+g1F7JVJKAi0s7FF3AgMBAAEw
DQYJKoZIhvcNAQELBQADQQBAVonvGIu1kc1p8hX/xSM+Cn9iBPBWdoDbA5S0JHE6
xk7KUyeUgPQImM3cbDNKGu8CZ9+gQMi11UqBenufdate
-----END CERTIFICATE-----
'''

pk = '''-----BEGIN PRIVATE KEY-----
MIIBVgIBADANBgkqhkiG9w0BAQEFAASCAUAwggE8AgEAAkEAsUBdVXQkfkw9+FkQ
wY1vUQKFe/TUf/F24SAXXgVG7cibX+i9JXF9frlxTsxzU1b9J6N2foNReyVSSgIt
LOxRdwIDAQABAkAwYqOXyiaUG3fnLVj3nQZAFPIfTkwbyOxss/ftAH/GNMJzSV3I
HENU4OPQgBvhWLXilBaFBHf2KWmmpTSryktRAiEA2SR8yJE3dFBfHqE09sodRztI
GntJIBLSHXlw2qBAlMsCIQDQ+G0rtRTAuquXi4HYRNEW3f2HjjBOKTMgb9nEjgCM
hQIhAJ728Us71GcYd6pKxiVtraV6Jr0MSGpsnNnrD81dyCmlAiEApZIQPa8uED5X
Mq2QZaCw4iNle4AHegZewfadXoT8nlkCIQDJnb9/tugPRXq+i6UDHSbbsQF1exGT
emU9vi+ojfuWlQ==
-----END PRIVATE KEY-----
'''

cert1 = ssl.PrivateCertificate.loadPEM(pk+c)
cert1a = ssl.Certificate.loadPEM(c)

certParams1 = {
    'tls_localCertificate': cert1,
    'tls_verifyAuthorities': [cert1a]
}
server_certs = {
    'some_sync_path_guid' : {
        'tls_localCertificate': cert1,
        'tls_verifyAuthorities': [cert1a]
    }
}

@defer.inlineCallbacks
def after_auth(success, client):

    d = yield client.callRemote(FilesResource, index = True)
    print d

    gg = yield MyFile.all()
    print 'My Files before delete'
    print gg

    print 'Do Delete'
    d = yield client.callRemote(FilesResource, delete = ['aa'])
    print d
    gg = yield MyFile.all()
    print 'My Files after delete'
    print gg


@defer.inlineCallbacks
def main():
    log.startLogging(sys.stdout)
    clean_temp_dir(create=True)
    yield initDB(db_path)

    print 'Load Key in db'
    sync_path = yield SyncPath(root='abdc', guid='abcdef').save()
    auth = yield Authorization(guid='some_guid', pk_str=pk, cert_str=c, sync_path_id=1).save()
    my_file = yield MyFile(path='aa', sync_path_id = 1, fhash = 'abcd', is_dir = False).save()

    print 'start_server'
    reactor.listenTCP(9991, ServerFactory())

    print 'start_client'
    cf = ClientFactory( authorization=auth, after_auth=after_auth)
    gg = reactor.connectTCP('localhost', 9991, cf)

main()
reactor.run()

