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
from .lib.util import time_now

import rainmaker_app
from rainmaker_app import app, lib, tasks, db, version, cli

def init_pre():
    '''
        pre init application
        - Instantiate global app variable
    '''
    global app
    # Start logging
    log.startLogging(sys.stdout, setStdout=False)
    # set root app directory
    app.root = path.root
    # set config search paths
    app.paths = [os.path.join(app.root, 'conf')]
    # load default config
    args = load('config.yml')
    app.add_attrs(args)
    # process cli
    cli_args = cli.parse(app, version)
    app.debug_script = None
    if 'debug_script_path' in cli_args:
        cli_args['start_console'] = True
        app.debug_script = load(cli_args['debug_script_path'], abspath=True)

    app.add_attrs(cli_args) 
    app.paths.insert(0, app.user_dir)
    # logging/monitor fs events
    from rainmaker_app.lib.fs_actions import FsActions
    app.fs = FsActions()
    # install?
    from rainmaker_app.tasks import install
    install.run()
    # process user config
    config_args = load(app.config_path, abspath=True)
    app.add_attrs(config_args)
    # reload cli args because they take precedence
    app.add_attrs(cli_args)

@defer.inlineCallbacks
def init_app():
    '''
        init db, install user dir, init networking
    '''
    global app
    
    # record start time
    app.running = True 
    app.started_at = time_now()
    app.run_loop = LoopingCall(_check_for_stop)
    app.run_loop.start(0.3)

    # create/init db run migrations 
    from rainmaker_app.db.config import initDB
    yield initDB(app.database_path)
    
    # configure tox
    from conf.initializers import tox
    yield tox.configure()

    # gen ephemeral auth
    log.msg('Generating key...')
    from .lib.net.ephemeral_auth import EphemeralAuth
    app.auth = EphemeralAuth(**app.auth_options)
    
    # scan folders
    from .model.sync_path import SyncPath
    sync_paths = yield SyncPath.all()
    for sync_path in sync_paths:
        sync_path.scan()
    print 'Initialization complete'

###############################################
def init_network():
    # late imports, needed to run init first
    from rainmaker_app.lib.net import start_tls, clients, dht_node 
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP 

    # init
    app.tcp_server = start_tls.ServerFactory(**app.tcp_server_options)
    app.udp_server = MulticastServerUDP(**app.udp_server_options)
    app.client = clients.ClientFactory.config(**app.tcp_client_options)

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

