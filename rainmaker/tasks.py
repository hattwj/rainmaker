# Python imports
from __future__ import print_function
import os

from rainmaker.db.main import init_db
from rainmaker import tox
import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def autorun(app):
    log.info("Starting rainmaker version: %s" % app.version)
    log.info('Checking installation...')
    # create user's config dir
    if not os.path.isdir(app.user_dir):
        did_install = True
        app.fs_log.mkdir(app.user_dir) 
        app.fs_log.touch(app.db_path)

    log.info('Initializing db...') 
    db = init_db(app.db_path)

    log.info('Configuring Tox...')
    # check db
    tox_servers = ToxServer.all()
    # load server data
    if not tox_servers:
        nodes = tox.tox_updater.fetch(opts.get('tox_html', None))
        if not nodes:
            log.error('Unable to find any nodes')
            exit()
        for ipv4, port, pubkey in nodes:
            server = yield ToxServer.findOrCreate(ipv4=ipv4, 
                port=port, pubkey=pubkey)
            tox_servers.append(server)
    if not tox_servers:
        log.error('Unable to find any nodes')
        exit()
    for ts in tox_servers:
        tox.tox_env.add_server(ts.ipv4, ts.port, ts.pubkey)
    log.info('Found %s tox servers' % len(tox_servers))


