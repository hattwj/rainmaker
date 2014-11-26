from . common import *
from . base import Base
from . my_file import MyFile

q_versions = '''
    SELECT m.id
    FROM my_files m
    JOIN sync_comparisons c
        ON m.next_id = %(my_file_id)s 
        AND c.sync_path_id IN %(sync_path_ids)s
    ORDER BY m.updated_at DESC;'''


class Difference(Base):
    sticky_table = True # don't allow console db clear
    
    q_difference = """
                SELECT DISTINCT m1.id AS my_file_id
                FROM my_files m1
                LEFT JOIN host_files m2
                    ON m1.path = m2.path
                    AND m1.sync_path_id =  
                    AND m2.sync_path_id = 
                    AND m1.fhash = m2.fhash 
                    AND m1.is_dir = m2.is_dir
                    AND m1.size = m2.size
                    AND m1.sync_path_id IN %(ids)s
                    AND m2.sync_path_id IN %(ids)s
                    AND m1.state = m2.state
                    AND m2.next_id IS NULL
                    AND m1.next_id IS NULL
                WHERE m2.id IS NULL
                    AND m1.next_id IS NULL
                    AND m1.sync_path_id IN %(ids)s;"""

    @classmethod
    @defer.inlineCallbacks
    def between_sync_paths(klass, *ids): 
        q = klass.q_difference % { 'ids' : sql_arr(ids) } 
        diffs = yield Registry.DBPOOL.runQuery( q )
        my_files = yield MyFile.find_many([d[0] for d in diffs if d])
        for my_file in my_files:
            my_file.versions = yield versions( my_file.id, ids )
        defer.returnValue( my_files )

@defer.inlineCallbacks
def versions(my_file_id, sync_path_ids):
    """ """
    q = q_versions % { 
        'my_file_id' : my_file_id, 
        'sync_path_ids' : sql_arr(sync_path_ids) 
    } 
    vers = yield Registry.DBPOOL.runQuery( q )
    if len(vers) == 0:
        defer.returnValue( None )
    my_files = yield MyFile.find_many( [v[0] for v in vers] )
    defer.returnValue( my_files )

def sql_arr(arr):
    ''' return array as str for use in sql query '''
    return "(%s)" % ','.join( [str(i) for i in arr] )
