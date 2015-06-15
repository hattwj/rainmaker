# Python imports
from __future__ import print_function
from sys import exit

# Lib imports
from twisted.internet import defer

# Local imports
from rainmaker.tox import tox_updater, tox_env
#from rainmaker.main import Application
from rainmaker.db.main import ToxServer
from rainmaker.tox.tox_ring import SyncBot, PrimaryBot
import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def init_tox(session, **opts):
    # check db
    tox_servers = session.query(ToxServer).all()
     
    # load server data
    if not tox_servers:
        log.info('Getting tox server contacts...')
        data = opts.get('tox_html')
        if data is None:
            log.info('Downloading fresh server info...')
            data = tox_updater.download()
        else:
            log.info('Loading cached server info...')

        # attempt to load
        if not data:
            log.error('Unable to find any nodes')
            exit()
        tox_servers = html_to_tox_servers(session, data)
        log.info('Found %s tox servers' % len(tox_servers))
    else:
        log.info('%s tox servers loaded' % len(tox_servers))
    
    tox_servers = session.query(ToxServer).all()   
    if len(tox_servers) == 0:
        log.error('Unable to find any valid nodes')
        exit()
    for ts in tox_servers:
        tox_env.add_server(ts.ipv4, ts.port, ts.pubkey)

def html_to_tox_servers(sess, html):
    tox_servers = []
    for ipv4, port, pubkey in tox_updater.parse_page(html):
        server = sess.query(ToxServer).filter(ToxServer.ipv4==ipv4).first()
        if not server:
            server = ToxServer(ipv4=ipv4)
        server.port=port
        server.pubkey=pubkey
        sess.add(server)
        tox_servers.append(server)
    sess.commit()
    return tox_servers
