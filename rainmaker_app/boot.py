import os
import sys
import yaml
import random
import base64

from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from twisted.python import log

from .lib.conf import load
from .lib import path
from .lib.attrs_bag import AttrsBag

import rainmaker_app
from rainmaker_app import app, lib, tasks, db, version

def init_pre():
    '''
        pre init application
    '''
    global app
    # Start logging
    log.startLogging(sys.stdout, setStdout=False)
    #log.startLogging(sys.stdout, setStdout=True)
    # set reactor, mark self as running
    app.reactor = reactor
    # set root app directory
    app.root = path.root
    app.paths = [os.path.join(app.root, 'conf')]
    # load default config
    args = load('config.yml')
    app.add_attrs(args)
    # process cli
    cli_args = cli_parse(app)
    app.add_attrs(cli_args) 
    app.paths.insert(0, app.user_dir)
    # logging/monitor fs events
    from rainmaker_app.lib.fs_actions import FsActions
    app.fs = FsActions()
    # install?
    from rainmaker_app.tasks import install
    install.run()
    # process user config
    args = load(app.config_path, abspath=True)
    app.add_attrs(args)
    app.add_attrs(cli_args)

@defer.inlineCallbacks
def init_app():
    '''
        init db, install user dir, init networking
    '''
    global app
    from rainmaker_app.db.config import initDB

    # create/init db run migrations 
    yield initDB(app.database_path)
    
    # record start time
    app.running = True 
    app.started_at = lib.util.time_now()
    app.run_loop = LoopingCall(_check_for_stop)
    app.run_loop.start(0.3)

    # gen ephemeral auth
    log.msg('Generating key...')
    from .lib.net.ephemeral_auth import EphemeralAuth
    app.auth = EphemeralAuth(**app.auth_options)

###############################################
def init_network():
    # late imports, needed to run init first
    from rainmaker_app.lib.net import start_tls, clients, dht_node 
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP  
    
    # init
    app.node = dht_node.DHTNode(app.auth)
    app.tcp_server = start_tls.ServerFactory(**app.tcp_server_options)
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
    app.tcp_server.start()

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
    from rainmaker_app.lib import logger
    parser = argparse.ArgumentParser(version=version, add_help=True)
    parser.add_argument('-i', action="store_true", dest='start_console', default=False)
    # set config  path
    parser.add_argument('-c', '--config', action="store", dest='config_path')
    # set user dir
    parser.add_argument('--dir', action="store", dest='user_dir')
    # don't log to screen
    parser.add_argument('-q','--quiet', action="store_true", dest='log.quiet')
    # set logfile path
    parser.add_argument('--log', 
        action="store", 
        dest='log.level', 
        choices=logger.levels.keys())
    # Dont broadcast
    parser.add_argument('--nobroadcast', 
        action="store_false", 
        dest='udp_server_options.broadcast')
    # Do broadcast
    parser.add_argument('--broadcast', 
        action="store_true",
        dest='udp_server_options.broadcast')
    # ephemeral key size
    parser.add_argument('-k', action="store", 
        dest='auth_options.key_size')
    # udp: listen_port, broadcast, multicast
    parser.add_argument('--udp-b', action="store", 
        dest='udp_server_options.broadcast_port')
    parser.add_argument('--udp', action="store", 
        dest='udp_server_options.listen_port')
    parser.add_argument('-m','--mgroup', action="store", 
        dest='udp_server_options.multicast_group')
    parser.add_argument('--tcp', action="store", 
        dest='tcp_server_options.listen_port')


    keys = ['udp_server_options.broadcast_port',
        'udp_server_options.listen_port',
        'tcp_server_options.listen_port',
        'auth_options.key_size']
    result = {}
    # parse args and convert result to dict
    kargs = vars( parser.parse_args(args) )
    for k, v in kargs.iteritems():
        if v:
            if k in keys:
                result[k] = int(v)
            else:
                result[k] = v
    return result
