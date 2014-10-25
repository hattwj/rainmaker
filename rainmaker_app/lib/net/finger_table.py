from threading import Lock
from twisted.internet import defer
from rainmaker_app import app
from . clients import ClientFactory

_hosts = {}
_hosts_lock = Lock()

host_ttl = 120

def all_hosts():
    return _hosts

def host_key(host):
    return host.signature

def add(host):
    result = False
    _hosts_lock.acquire()
    #try:
    key = host_key(host)
    if key and key not in _hosts:
        _hosts[key] = host
        ClientFactory.ping(host.addr_port)
        app.reactor.callLater(host_ttl, remove_if_stale, host)
        result = True
    #except: 
    #    pass
    _hosts_lock.release()
    return result

def get(host):
    _hosts_lock.acquire()
    result = None
    try:
        key = host_key(host)
        if key in _hosts:
            result = _hosts[key] 
    except: 
        pass
    _hosts_lock.release()
    return result

def exists(host):
    return get(host) != None

def stale(host):
    host = get(host)
    if host and not host.is_stale:
        return True
    return False

def remove(host):
    _hosts_lock.acquire()
    result = False
    try:
        key = host_key(host)
        if key in _hosts:
            del(_hosts[key])
            result = True
    except: 
        pass
    _hosts_lock.release()
    return result

def remove_if_stale(host):
    host = get(host)
    if not host:
        return
    _hosts_lock.acquire()
    result = False
    try:
        key = host_key(host)
        if key in _hosts and host.is_stale:
            del(_hosts[key])
            result = True
    except: 
        pass
    _hosts_lock.release()
    app.reactor.callLater(host_ttl, remove_if_stale, host)
