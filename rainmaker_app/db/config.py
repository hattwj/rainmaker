from twisted.enterprise import adbapi
from twisted.internet import defer
from twistar.dbobject import DBObject
from twistar.registry import Registry

from rainmaker_app.lib import logger
from . models import *

log = logger.create('Database')

MIGRATIONS = {
    0 : """CREATE TABLE schema_migrations (version TEXT)""",
    1 : """ CREATE TABLE sync_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root TEXT NOT NULL,
                guid TEXT,
                scanned_at INTEGER
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
            )""",
    4 : """ CREATE TABLE sync_comparisons (
                my_file_id INTEGER, 
                sync_path_id INTEGER
            )""",
    5 : """ CREATE VIEW differences AS
                SELECT DISTINCT m1.id AS my_file_id
                FROM my_files m1
                LEFT JOIN my_files m2
                    ON m1.path = m2.path
                    AND m1.sync_path_id != m2.sync_path_id
                    AND m1.fhash = m2.fhash 
                    AND m1.is_dir = m2.is_dir
                    AND m1.size = m2.size
                    AND m1.state = m2.state
                WHERE m2.id IS NULL
                    AND m1.next_id IS NULL
                    AND m2.next_id IS NULL""" 
}

@defer.inlineCallbacks
def _migrate( versions=[] ):
    """ 
        Run migrations 
        - except for values in 'versions' array
    """
    if versions == None:
        versions = []

    for k, v in MIGRATIONS.iteritems():
        if str(k) in versions:
            log.info( 'Skipping migration %s' % k)
            pass
        else:
            log.info( 'Running migration %s' % k)
            yield Registry.DBPOOL.runQuery(v)
            yield SchemaMigration(version=k).save()

@defer.inlineCallbacks
def _check_schema():
    q = """SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';"""
    name = yield Registry.DBPOOL.runQuery(q)

    versions = []
    
    if name:
        q = """SELECT version FROM schema_migrations"""
        result = yield Registry.DBPOOL.runQuery(q)
        
        # collapse array of tuples to array
        for tup in result:
            versions.append( tup[0] )
        
        if '0' not in versions:
            versions.append('0') # dont create schema migrations table

    defer.returnValue( versions )
    
def initDB(location):
    Registry.DBPOOL = adbapi.ConnectionPool(
        'sqlite3', 
        location, 
        check_same_thread=False,
        cp_min=1,
        cp_max=1
    )  # max db thread to 1 for sqlite

    Registry.register( *models )
    g = _check_schema()
    g.addCallback(_migrate)
    return g

def tearDownDB():
    return defer.succeed(True)
