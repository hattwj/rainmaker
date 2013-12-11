from threading import Lock
from rainmaker_app.model.pubkey import *

class Broadcast(Base):
    BELONGSTO = ['host', 'message']
    BEFORE_CREATE = ['send_broadcast']
    _listeners = {}
    _lock = Lock()

    @classmethod
    def send(self, msg):
        pass

    @classmethod
    def add_listener(klass, conx):
        klass._lock.aquire()
        h = hash[ conx ]
        klass._listeners[ h ] = conx
        klass.lock.release()
    
    @classmethod
    def remove_listener(klass, conx):
        klass._lock.aquire()
        klass._listeners.pop( hash(conx) )
        klass.lock.release()

Broadcast.validatesUniquenessOf('host_id','message_id')
Broadcast.validatesPresenceOf('host_id','message_id')
