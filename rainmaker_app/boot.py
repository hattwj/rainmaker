import os
import yaml
import random
import base64

from twisted.internet import reactor

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

def init():
    ''' '''
    global app
    # process cli
    args = cli_parse(app)
    app.add_attrs(args)
 
    # install?
    tasks.install(app.user_dir)
    app.fs.touch(app.config_path)

    # process user config
    args = load(app.config_path, abspath=True) 
    app.add_attrs(args)

    # init logging
    #logger.create('root', app.log_style, app.log_level)
    #logger.log_to_file( app.log_path, 'root' )

    # create/init db run migrations 
    initDB(app.database_path)

###############################################
def start_network():
    from rainmaker_app.lib.net.udp_multicast import MulticastServerUDP  
    opts = app.udp_server_options 
    udp_server = MulticastServerUDP(**opts) 
    app.reactor.listenMulticast(opts['listen_port'], udp_server) 
    print 'UDP server listening on port %s' % opts['listen_port']
    
    udp_server.broadcast_loop()
    print 'UDP broadcasting on port %s' % app.udp_server_options['broadcast_port']

    from rainmaker_app.lib.net import start_tls
    app.reactor.listenTCP(app.tcp_port, start_tls.ServerFactory())
    print 'TCP Server listening on port %s' % app.tcp_port
  
    print 'net done. Waiting...'

import argparse
def cli_parse(app):
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
    parser.add_argument('--broadcast', 
        action="store_true", 
        default=app.udp_server_options['broadcast'], 
        dest='udp_server_options.broadcast')
    # udp: listen_port, broadcast, multicast
    parser.add_argument('--udp-b', action="store", 
        dest='udp_server_options.broadcast_port', 
        default=app.udp_server_options['broadcast_port'])
    parser.add_argument('--udp', action="store", 
        dest='udp_server_options.listen_port', 
        default=app.udp_server_options['listen_port'])
    parser.add_argument('-m','--multicast', action="store", 
        dest='udp_server_options.multicast_group', 
        default=app.udp_server_options['multicast_group'])
    parser.add_argument('--tcp', action="store", 
        dest='tcp_port', 
        default=app.tcp_port)

    # tcp: port
    # config path
    # web_ui: username, password

    # parse args and convert result to dict
    args = vars( parser.parse_args() )
    # make sure port is an integer
    args['udp_server_options.broadcast_port'] = int(args['udp_server_options.broadcast_port'])
    args['udp_server_options.listen_port'] = int(args['udp_server_options.listen_port'])
    args['tcp_port'] = int(args['tcp_port']) 
    return args

