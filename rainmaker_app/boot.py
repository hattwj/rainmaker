import os
import sys
import yaml
import random
import base64

from twisted.internet import reactor, defer
from twisted.python import log

from .lib.conf import load
from .lib import logger, path, AttrsBag

import rainmaker_app
from rainmaker_app.db.config import initDB
from rainmaker_app import app, lib, tasks, db

def pre_init():

    # set base attributes
    app_attrs = load('rainmaker_app.yml')
    app.add_attrs( app_attrs )

    # generate app guid    
    app.guid = base64.b64encode( str(random.getrandbits(64)) )
    
    # set reactor, mark self as running
    app.running = True 
    app.reactor = reactor

    # set root app directory
    app.root = path.root

    # logging/monitor fs events
    app.fs = lib.FsActions()

    # process cli
    args = cli_parse(app)
    app.add_attrs(args)

    # Start logging
    log.startLogging(sys.stdout)

    # install?
    tasks.install(app.user_dir)
    app.fs.touch(app.config_path)
    
    # process user config
    args = load(app.config_path, abspath=True) 
    app.add_attrs(args)

    # init logging
    #logger.create('root', app.log_style, app.log_level)
    #logger.log_to_file( app.log_path, 'root' )


@defer.inlineCallbacks
def init():
    ''' parse command line and load config'''
    global app

    # create/init db run migrations 
    yield initDB(app.database_path)
    
    # record start time
    app.started_at = lib.util.time_now()

    from .db.models import Authorization
    app.auth = Authorization(**app.auth_options)

    # start listening/searching/syncing
    start_network()

###############################################
def start_network():
    # late imports, needed to run init first
    from rainmaker_app.lib.net import start_tls, clients, dht_node 
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP  
    
    # init
    app.node = dht_node.DHTNode(**app.dht_node_options)
    app.server = start_tls.ServerFactory(**app.tcp_server_options)
    app.udp_server = MulticastServerUDP(**app.udp_server_options)
    app.client = clients.ClientFactory(**app.tcp_client_options)

    # start lan discovery
    app.udp_server.start()
    
    # start main server
    app.server.start()

    # start dht node
    app.node.start()
    print 'net done. Waiting...'

import argparse
def cli_parse(app):
    ''' command line parser '''
    parser = argparse.ArgumentParser(version=app.version, add_help=True)
    # set config  path
    parser.add_argument('-c', '--config', action="store", dest='config_path', default=app.get('config_path'))
    # don't log to screen
    parser.add_argument('-q','--quiet', action="store_true", dest='log.quiet',default=False)
    # set logfile path
    parser.add_argument('--log', 
        action="store", 
        dest='log.level', 
        choices=app.log_levels, 
        default='warn')
    # Dont broadcast
    parser.add_argument('--nobroadcast', 
        action="store_false", 
        default=app.udp_server_options['broadcast'], 
        dest='udp_server_options.broadcast')
    # Do broadcast
    parser.add_argument('--broadcast', 
        action="store_true", 
        default=app.udp_server_options['broadcast'], 
        dest='udp_server_options.broadcast')
    # ephemeral key size
    parser.add_argument('-k', action="store", 
        dest='auth_options.key_size', 
        default=app.auth_options['key_size'])
    # udp: listen_port, broadcast, multicast
    parser.add_argument('--udp-b', action="store", 
        dest='udp_server_options.broadcast_port', 
        default=app.udp_server_options['broadcast_port'])
    parser.add_argument('--udp', action="store", 
        dest='udp_server_options.listen_port', 
        default=app.udp_server_options['listen_port'])
    parser.add_argument('-m','--mgroup', action="store", 
        dest='udp_server_options.multicast_group', 
        default=app.udp_server_options['multicast_group'])
    parser.add_argument('--tcp', action="store", 
        dest='tcp_server_options.listen_port', 
        default=app.tcp_server_options['listen_port'])

    # parse args and convert result to dict
    args = vars( parser.parse_args() )
    # make sure port is an integer
    args['udp_server_options.broadcast_port'] = int(args['udp_server_options.broadcast_port'])
    args['udp_server_options.listen_port'] = int(args['udp_server_options.listen_port'])
    args['tcp_server_options.listen_port'] = int(args['tcp_server_options.listen_port']) 
    args['auth_options.key_size'] = int(args['auth_options.key_size']) 
    return args
