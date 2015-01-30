from twisted.enterprise import adbapi
from twisted.internet import defer
from twisted.python import log
from twistar.dbobject import DBObject
from twistar.registry import Registry

from rainmaker_app.lib import logger
from rainmaker_app.db.models import *

log = logger.create(__name__)

MIGRATIONS = {
    0 : """CREATE TABLE schema_migrations (version TEXT)""",
    1 : """ CREATE TABLE sync_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root TEXT NOT NULL,
                password_rw TEXT NOT NULL,
                guid TEXT,
                scanned_at INTEGER,
                rolling_hash TEXT,
                state_hash TEXT,
                state_hash_updated_at INTEGER,
                scanning BOOLEAN,
                listening BOOLEAN,
                updating BOOLEAN
            )""",
    2 : """ CREATE TABLE my_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_path_id INTEGER NOT NULL,
                path TEXT NOT NULL, 
                fhash TEXT, 
                size INTEGER DEFAULT 0, 
                inode INTEGER, 
                state INTEGER, 
                mtime INTEGER, 
                ctime INTEGER, 
                is_dir BOOLEAN NOT NULL,
                next_id INTEGER,
                created_at INTEGER,
                updated_at INTEGER, 
                scanned_at INTEGER
            )""", # TODO: try: created_at DEFAULT (datetime('now','localtime'))
    3 : """ CREATE TABLE sync_comparisons (
                my_file_id INTEGER, 
                host_sync_path_id INTEGER
            )""",
    4 : """ CREATE TABLE authorizations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_path_id INTEGER NOT NULL,
                cert_str TEXT NOT NULL,
                pk_str TEXT NOT NULL,
                pubkey_str TEXT
            )""",
    5 : """ CREATE TABLE pubkeys(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pubkey_str TEXT NOT NULL
            )""",
    6 : """ CREATE TABLE hosts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_path_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                udp_port INTEGER NOT NULL,
                tcp_port INTEGER NOT NULL,
                tox_pubkey TEXT,
                pubkey_str TEXT,
                cert_str TEXT,
                signature TEXT,
                signed_at INTEGER,
                created_at INTEGER,
                last_contacted_at INTEGER
            )""",
    7 : """ CREATE TABLE host_sync_paths( 
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                sync_path_id INTEGER NOT NULL,
                rolling_hash TEXT,
                state_hash TEXT,
                machine_name TEXT NOT NULL
            )""",
    8 : """ CREATE TABLE host_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_sync_path_id INTEGER NOT NULL,
                path TEXT NOT NULL, 
                fhash TEXT, 
                size INTEGER DEFAULT 0, 
                state INTEGER, 
                is_dir BOOLEAN NOT NULL,
                created_at INTEGER,
                updated_at INTEGER,
                next_id INTEGER
            )""", # TODO: try: created_at DEFAULT (datetime('now','localtime'))
    9 : """ CREATE VIEW differences AS
                SELECT DISTINCT 
                    m1.id AS my_file_id,
                    hsp.id AS host_sync_path_id
                FROM my_files m1
                LEFT JOIN host_sync_paths hsp
                    ON hsp.sync_path_id = m1.sync_path_id
                LEFT JOIN host_files m2
                    ON m1.path = m2.path
                    AND m1.fhash = m2.fhash 
                    AND m1.is_dir = m2.is_dir
                    AND m1.size = m2.size
                    AND m1.state = m2.state
                WHERE m2.id IS NULL
                    AND m1.next_id IS NULL
                    AND m2.next_id IS NULL""",
    10 : ''' CREATE TABLE tox_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ipv4 TEXT NOT NULL,
                port INTEGER NOT NULL,
                pubkey TEXT NOT NULL
            )
    '''
}

@defer.inlineCallbacks
def _init_migrations( versions=[] ):
    """ 
        Run migrations 
        - except for values in 'versions' array
    """
    if versions == None:
        versions = []
    
    for k, v in MIGRATIONS.iteritems():
        if str(k) in versions:
            log.debug( 'Skipping migration %s' % k)
        else:
            log.info( 'Running migration %s' % k)
            log.debug(v)
            yield Registry.DBPOOL.runQuery(v)
            yield SchemaMigration(version=k).save()

@defer.inlineCallbacks
def _check_schema():
    q = """
    SELECT name 
    FROM sqlite_master 
    WHERE type='table' 
        AND name='schema_migrations';
    """
    name = yield Registry.DBPOOL.runQuery(q)
    #hold ver names
    versions = []
    # see if we found the table
    if name:
        q = """SELECT version FROM schema_migrations"""
        result = yield Registry.DBPOOL.runQuery(q)
        # collapse array of tuples to array
        for tup in result:
            versions.append( tup[0] )
        # schema migration table doesn't get a version
        if '0' not in versions:
            versions.append('0') # dont create schema migrations table
    # return schema versions that already exist
    defer.returnValue( versions )

def _db_connect(location):
    Registry.DBPOOL = adbapi.ConnectionPool(
        'sqlite3', 
        location, 
        check_same_thread=False,
        cp_min=1,
        cp_max=1
    )  # max db thread to 1 for sqlite

@defer.inlineCallbacks
def _init_models(*args):
    ''' modify each model'''
    for m in models_arr:
        yield _model_introspection(m)

@defer.inlineCallbacks
def _model_introspection(model):
    ''' create columns variable and init fields '''
    q = "PRAGMA table_info('%s')" % model.tablename()
    cols_tup = yield Registry.DBPOOL.runQuery(q)
    cols = [tup[1] for tup in cols_tup]
    model.columns = cols
    for col in cols:
        if not hasattr(model, col):
            setattr(model, col, None)

def _init_failed(reason):
    import sys
    log.error(reason.getTraceback())
    sys.exit(1)

def initDB(location):
    ''' init db connection and models '''
    _db_connect(location)
    Registry.register( *models_arr )
    g = _check_schema()
    g.addCallback(_init_migrations)
    g.addCallback(_init_models)
    g.addErrback(_init_failed)
    return g

def tearDownDB():
    return defer.succeed(True)

