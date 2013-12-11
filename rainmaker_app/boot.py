import os
import yaml
import random
import base64

from twisted.internet import reactor

from .lib.conf import load
from .lib import logger, path, AttrsBag
from .app import initialize

import rainmaker_app
from rainmaker_app import app

def pre_init():
    
    app.guid = base64.b64encode( str(random.getrandbits(64)) ) 
    print app.guid
    app.running = True 
    app.reactor = reactor

    # set root app directory
    app.root = path.root
    
    # set base attributes
    app_attrs = load('rainmaker_app.yml')
    for k, v in app_attrs.iteritems():
        setattr(app, k, v)

###############################################
def start_network():
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP, broadcast_loop, MulticastClientUDP 
    print 'Starting UDP server'
    app.udp_server = app.reactor.listenMulticast(app.udp_port, MulticastServerUDP())        
    app.udp_broadcast = app.reactor.listenUDP(0, MulticastClientUDP())
    #.write(request, (app.multicast_group, app.udp_port)) 

    from rainmaker_app.lib.net import start_tls
    print 'Starting TCP Server'
    app.reactor.listenTCP(app.tcp_port, start_tls.ServerFactory())

    print 'Starting UDP broadcast loop'
    broadcast_loop()

    print 'net done. Waiting...'
