from twisted.enterprise import adbapi
from twisted.internet import defer

from .model import * #SchemaMigration

MIGRATIONS = {
    0 : """CREATE TABLE schema_migrations (version TEXT)""",
    1 : """CREATE TABLE sync_paths (id INTEGER PRIMARY KEY AUTOINCREMENT,
            root TEXT, scanned_at INTEGER)""",
    2 : """CREATE TABLE my_files (id INTEGER PRIMARY KEY AUTOINCREMENT,
            mtime INTEGER, ctime INTEGER, sync_path_id INTEGER, path TEXT, fhash TEXT, 
            size INTEGER, inode INTEGER, state INTEGER, created_at INTEGER,
            updated_at INTEGER, scanned_at INTEGER, is_dir BOOLEAN,
            UNIQUE(sync_path_id, path) ON CONFLICT REPLACE )""",
    3 : """CREATE TABLE file_versions (my_file_id INTEGER PRIMARY KEY,
            sync_path_id INTEGER, path TEXT, fhash TEXT, 
            size INTEGER, inode INTEGER, state INTEGER, created_at INTEGER,
            is_dir BOOLEAN, version INTEGER, parent_id INTEGER,
            UNIQUE(sync_path_id, path, version) ON CONFLICT ROLLBACK)""",
    4 : """CREATE VIEW differences AS
               SELECT DISTINCT m1.*
               FROM my_files m1
               LEFT JOIN my_files m2
                   ON m1.path = m2.path
                   AND m1.sync_path_id != m2.sync_path_id
                   AND m1.fhash = m2.fhash 
                   AND m1.is_dir = m2.is_dir
                   AND m1.size = m2.size
                   AND m1.state = m2.state
               WHERE m2.id IS NULL"""
}

@defer.inlineCallbacks
def _migrate( versions=[] ):

    if versions == None:
        versions = []

    for k, v in MIGRATIONS.iteritems():
        if str(k) in versions:
            print 'Skipping migration %s' % k
        else:
            print 'Running migration %s' % k
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
    g = _check_schema()
    g.addCallback(_migrate)
    return g

def tearDownDB():
    return defer.succeed(True)
