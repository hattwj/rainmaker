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
        [session.add(ts) for ts in html_to_tox_servers(data)]
        session.commit()
        log.info('Found %s tox servers' % len(tox_servers))
    else:
        log.info('%s tox servers loaded' % len(tox_servers))
    
    tox_servers = session.query(ToxServer).all()   
    if not tox_servers:
        log.error('Unable to find any valid nodes')
        exit()
    for ts in tox_servers:
        tox_env.add_server(ts.ipv4, ts.port, ts.pubkey)

def html_to_tox_servers(html):
    tox_servers = []
    for ipv4, port, pubkey in tox_updater.parse_page(html):
        server = ToxServer(ipv4=ipv4, 
            port=port, pubkey=pubkey)
        tox_servers.append(server)
    return tox_servers
