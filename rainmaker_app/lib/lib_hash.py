import hashlib

def md5Checksum(path, chunk_size=8192):
    m = hashlib.md5()
    fh = open(path, 'rb')
    while True:
        data = fh.read(chunk_size)
        if not data:
            break
        m.update(data)
    fh.close()
    return m.hexdigest()


class RollingHash(object):
    def __init__(self, hexdigest=None):
        self._hexdigest = hexdigest

    def update(self, msg):
        m = hashlib.md5()
        m.update('%s%s' % (str(self._hexdigest), msg) )
        self._hexdigest = m.hexdigest()

    def hexdigest(self):
        return self._hexdigest
