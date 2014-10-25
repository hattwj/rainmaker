from threading import Lock

_conns = {}
_conns_lock = Lock()

def conn_key(conn):
    return ''.join(conn.addr_port)

def add(conn):
    _conns_lock.acquire()
    try:
        key = conn_key(conn)
        _conns[key] = conn 
    except: 
        pass
    _conns_lock.release()

def get(conn):
    _conns_lock.acquire()
    result = None
    try:
        key = conn_key(conn)
        if key in _conns:
            result = _conns[key] 
    except: 
        pass
    _conns_lock.release()
    return result

def active(conn):
    return get(conn) == None

def stale(conn):
    return not active(conn)

def remove(conn):
    _conns_lock.acquire()
    result = False
    try:
        key = conn_key(conn)
        if key in _conns:
            del(_conns[key])
            result = True
    except: 
        pass
    _conns_lock.release()
    return result
