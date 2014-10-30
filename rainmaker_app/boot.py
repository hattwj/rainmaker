import os
import sys
import yaml
import random
import base64

from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from twisted.python import log

from .lib.conf import load
from .lib import logger, path, AttrsBag

import rainmaker_app
from rainmaker_app.db.config import initDB
from rainmaker_app import app, lib, tasks, db

def init_pre():
    '''
        pre init application
    '''
    global app

    # set base attributes
    app_attrs = load('rainmaker_app.yml')
    app.add_attrs( app_attrs )

    # set reactor, mark self as running
    app.reactor = reactor

    # set root app directory
    app.root = path.root

    # logging/monitor fs events
    app.fs = lib.FsActions()

def init_cli(args=None):
    # process cli
    global app
    args = cli_parse(app, args)
    app.add_attrs(args)

@defer.inlineCallbacks
def init_app():
    '''
        init db, install user dir, init networking
    '''
    global app

    # Start logging
    log.startLogging(sys.stdout, setStdout=False)
    #log.startLogging(sys.stdout, setStdout=True)

    # install?
    tasks.install(app.user_dir)
    app.fs.touch(app.config_path)
    
    # process user config
    args = load(app.config_path, abspath=True) 
    app.add_attrs(args)

    # create/init db run migrations 
    yield initDB(app.database_path)
    
    # record start time
    app.running = True 
    app.started_at = lib.util.time_now()
    app.run_loop = LoopingCall(_check_for_stop)
    app.run_loop.start(0.3)

    # gen ephemeral auth
    log.msg('Generating key...')
    from .db.models import Authorization
    app.auth = Authorization(**app.auth_options)

###############################################
def init_network():
    # late imports, needed to run init first
    from rainmaker_app.lib.net import start_tls, clients, dht_node 
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP  
    
    # init
    app.node = dht_node.DHTNode(app.auth)
    app.server = start_tls.ServerFactory(**app.tcp_server_options)
    app.udp_server = MulticastServerUDP(**app.udp_server_options)
    app.client = clients.ClientFactory.config(**app.tcp_client_options) 
    app.udp_server.dht = app.node

def start_network():
    '''
        start networking
    '''
    # start lan discovery
    app.udp_server.start()
    
    # start main server
    app.server.start()

    # start dht node
    app.node.start()
    print 'net done. Waiting...'

def stop_app():
    global app
    app.running = False

def _check_for_stop():
    global app
    if not app.running:
        app.run_loop.stop()
        app.reactor.stop()

import argparse
def cli_parse(app, args=None):
    ''' 
        command line parser
    '''
    parser = argparse.ArgumentParser(version=app.version, add_help=True)
    parser.add_argument('-i', action="store_true", dest='start_console', default=False)
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
    args = vars( parser.parse_args(args) )
    # argument post processing
    args['udp_server_options.broadcast_port'] = int(args['udp_server_options.broadcast_port'])
    args['udp_server_options.listen_port'] = int(args['udp_server_options.listen_port'])
    args['tcp_server_options.listen_port'] = int(args['tcp_server_options.listen_port']) 
    args['auth_options.key_size'] = int(args['auth_options.key_size']) 
    return args
