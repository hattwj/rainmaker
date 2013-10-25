
from OpenSSL import crypto, SSL
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join

trusted = []

def verifyCallback(connection, x509, errnum, errdepth, ok):
    ''' validate certificate '''
    if not ok:
        print 'invalid cert from subject:', x509.get_subject()
        return False
    else:
        print "Server: Client certs are fine"
    return True

def create_self_signed_cert(size=2048):
    """
    """
            
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, size)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'us'
    cert.get_subject().ST = 'here'
    cert.get_subject().L = 'there'
    cert.get_subject().O = 'them'
    cert.get_subject().OU = 'and'
    cert.get_subject().CN = 'stuff'
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    #open(join(cert_dir, CERT_FILE), "wt").write(
    #    crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    #open(join(cert_dir, KEY_FILE), "wt").write(
    #    crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    f_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    f_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, k)
    
    return [f_key, f_cert]
