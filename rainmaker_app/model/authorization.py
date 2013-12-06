from twisted.internet  import defer, ssl
from rainmaker_app.model.common import *
from rainmaker_app.lib.net.cert import create_cert 

class Authorization(Base):
    BELONGSTO = ['sync_path']
    BEFORE_CREATE = ['generate_cert']
    
    def private_cert(self):
        return ssl.PrivateCertificate.loadPEM(self.pk_str+self.cert_str)
        
    def certificate(self):
        return ssl.Certificate.loadPEM(self.cert_str)

    def certParams(self, for_server=False):
        return paramify( self.private_cert(), self.certificate() )

    def generate_cert(self, force=False, key_size=2048):
        if force==False and self.pk_str and self.cert_str and self.guid:
            return True
        self.pk_str, self.cert_str = create_cert(key_size)
        self.guid = self.certificate.getPublicKey().keyHash()
        return True

def paramify( private_cert, *certs):
    return {
        'tls_localCertificate': private_cert,
        'tls_verifyAuthorities': certs
    }

