from OpenSSL import crypto, SSL
from time import gmtime, mktime

def verifyCallback(connection, x509, errnum, errdepth, ok):
    ''' validate certificate '''
    if not ok:
        print 'invalid cert from subject:', x509.get_subject()
        return False
    else:
        print "Server: Client certs are fine"
    return True

def create_cert(size=2048, as_objects=False):
    """
        Create a certificate and a private/public key pair
    """
            
    # create a key pair
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, size)

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
    cert.set_pubkey(pkey)
    cert.sign(pkey, 'sha256')
   
    # Convert the objects to PEM encoded strings
    if not as_objects:
        # Return the cert and pkey as PEM encoded strings
        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
        pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
    return [cert, pkey]

def pkey_str_to_pubkey_str(pkey_str):
    from Crypto.PublicKey import RSA
    pkey = RSA.importKey(pkey_str) 
    pubkey = pkey.publickey()
    
    # We have created the pubkey
    return pubkey.exportKey()       

#https://launchkey.com/docs/api/encryption
def encrypt_RSA(pubkey_str, message):
    '''
    param: public_key_loc Path to public key
    param: message String to be encrypted
    return base64 encoded encrypted string
    '''
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    #key = open(public_key_loc, "r").read()
    pubkey = RSA.importKey(pubkey_str)
    rsakey = PKCS1_OAEP.new(pubkey)
    encrypted = rsakey.encrypt(message)
    return encrypted.encode('base64')

def decrypt_RSA(pkey_str, package):
    '''
    param: public_key_loc Path to your private key
    param: package String to be decrypted
    return decrypted string
    '''
    from Crypto.PublicKey import RSA 
    from Crypto.Cipher import PKCS1_OAEP 
    from base64 import b64decode 
    #key = open(private_key_loc, "r").read() 
    pkey = RSA.importKey(pkey_str) 
    rsakey = PKCS1_OAEP.new(pkey) 
    decrypted = rsakey.decrypt(b64decode(package)) 
    return decrypted

def sign_data(pkey_str, data):
    '''
    param: private_key_loc Path to your private key
    param: package Data to be signed
    return: base64 encoded signature
    '''
    from Crypto.PublicKey import RSA 
    from Crypto.Signature import PKCS1_v1_5 
    from Crypto.Hash import SHA256 
    from base64 import b64encode, b64decode 
    #key = open(private_key_loc, "r").read() 
    rsakey = RSA.importKey(pkey_str) 
    signer = PKCS1_v1_5.new(rsakey) 
    digest = SHA256.new() 
    # It's being assumed the data is base64 encoded, so it's decoded before updating the digest 
    #digest.update(b64decode(data)) 
    digest.update(data) 
    sign = signer.sign(digest) 
    return b64encode(sign)

def verify_sign(pubkey_str, signature, data):
    '''
    Verifies with a public key from whom the data came that it was indeed 
    signed by their private key
    param: public_key_loc Path to public key
    param: signature String signature to be verified
    return: Boolean. True if the signature is valid; False otherwise. 
    '''
    from Crypto.PublicKey import RSA 
    from Crypto.Signature import PKCS1_v1_5 
    from Crypto.Hash import SHA256 
    from base64 import b64decode 
    #pub_key = open(public_key_loc, "r").read() 
    rsakey = RSA.importKey(pubkey_str) 
    signer = PKCS1_v1_5.new(rsakey) 
    digest = SHA256.new() 
    # Assumes the data is base64 encoded to begin with
    #digest.update(b64decode(data)) 
    digest.update(data) 
    if signer.verify(digest, b64decode(signature)):
        return True
    return False
