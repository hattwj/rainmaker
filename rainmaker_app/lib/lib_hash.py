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
