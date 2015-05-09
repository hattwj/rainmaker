# Python imports
from __future__ import print_function
import os

# Lib imports

# App imports
import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def setup_install(app):
    did_install = False
    # create user's config dir
    if not os.path.isdir(app.user_dir):
        did_install = True
        app.fs_log.mkdir(app.user_dir) 
    # create sub dirs too
    for p in ['tmp','plugins','log']:
        ipath = os.path.join(app.user_dir, p)
        if not os.path.isdir( ipath ):
            app.fs_log.mkdir(ipath)
    if not os.path.exists(app.user_conf_path):
        app.fs_log.copy(app.root_conf_path, app.user_conf_path)
    return did_install

def init_db(app):
    # create/init db run migrations 
    from rainmaker.db.config import initDB
    log.info('Initializing Database')
    return initDB(os.path.join(app.root, 'rainmaker.sqlite'))

def init_loop(app):
    def _check_for_stop():
        if app.stopping:
            run_loop.stop()
    # record start time
    app.running = True 
    app.started_at = time_now()
    run_loop = LoopingCall(_check_for_stop)
    return run_loop.start(0.5)

def setup_tox(app):
    from rainmaker import tox
    from rainmaker_app.models import ToxServer
    log.info('Configuring Tox')
    # check db
    tox_servers = yield ToxServer.all()
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

def auto_run(app):
    log.info('Starting...')
    setup_install(app)
    d = init_db(app)
    d.addCallback(setup_tox, app)
    d.addCallback(init_loop, app)

