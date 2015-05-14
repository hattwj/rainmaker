import os
import yaml
import pprint
pp = pprint.PrettyPrinter(indent=2, depth=6).pprint

from rainmaker.tests import test_helper
from rainmaker.db.main import init_db, HostFile, SyncFile
from rainmaker.db import views
from rainmaker.sync_manager import resolver

raw_data = test_helper.load(os.path.join('fixtures', 
    'unit', 'sync_manager', 'resolver_test.yml'))
test_data = yaml.safe_load(raw_data)

# Test Preparation 
def setup():
    test_helper.clean_temp_dir()

def teardown():
    pass
        


# Tests
def test_complex_sync():
    Run('complex_sync').expect([
        [resolver.THEIRS_CHANGED, resolver.DELETED, 1, 1],
        [resolver.THEIRS_CHANGED, resolver.DELETED, 2, 2],
        [resolver.MINE_CHANGED, resolver.MOVED, 3, 3],
        [resolver.MINE_CHANGED, resolver.MOVED, 4, 4],
        [resolver.THEIRS_CHANGED, resolver.MODIFIED, 5, 5],
        [resolver.MINE_CHANGED, resolver.NEW, 6, None],
        [resolver.MINE_CHANGED, resolver.NEW, 7, None],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 6],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 7],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 8]
    ])

# Tests
def test_deleted_no_conflict():
    Run('deleted_no_conflict').expect([
        [resolver.THEIRS_CHANGED, resolver.DELETED, 1, 1],
        [resolver.THEIRS_CHANGED, resolver.DELETED, 3, 3]
    ])

def test_modified_no_conflict():
    Run('modified_no_conflict').expect([
        [resolver.THEIRS_CHANGED, resolver.MODIFIED, 1, 1],
        [resolver.THEIRS_CHANGED, resolver.MODIFIED, 2, 2],
    ])

def test_moved_no_conflict():
    Run('moved_no_conflict').expect([
        [resolver.THEIRS_CHANGED, resolver.MOVED, 1, 1],
        [resolver.THEIRS_CHANGED, resolver.MOVED, 2, 2]
    ])

def test_new_no_conflict():
    Run('new_no_conflict').expect([
        [resolver.MINE_CHANGED, resolver.NEW, 1, None],
        [resolver.MINE_CHANGED, resolver.NEW, 2, None],
        [resolver.MINE_CHANGED, resolver.NEW, 3, None],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 1],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 2],
        [resolver.THEIRS_CHANGED, resolver.NEW, None, 3]
    ])

def test_conflict_modified():
    Run('conflict_modified').expect([
        [resolver.CONFLICT, resolver.MODIFIED, 1, 1],
        [resolver.CONFLICT, resolver.MODIFIED, 2, 2]
    ])

def test_renamed_conflict():
    Run('renamed_conflict').expect([
        [resolver.CONFLICT, resolver.MOVED, 1, 1]
    ])

class Run(object):
    def __init__(self, test_name):
        session = init_db()
        test_helper.load_fixture(session, test_name, test_data)
        self.session = session

    def expect(self, expected):
        sync_files, host_files = views.sync_diff(self.session, 1, 1)
        assert len(sync_files) > 0
        assert len(host_files) > 0
        #pp(host_files)
        #pp(sync_files)
        # process all new files
        while len(sync_files) > 0 or len(host_files) > 0:    
            r = resolver.resolve_files(sync_files, host_files)
            #pp(r)
            result = [r.status, r.state]
            result.append(r.sync_file.id if r.sync_file else None)
            result.append(r.host_file.id if r.host_file else None)
            #pp(expected)
            #pp(result)
            assert result in expected 

def myfd(m):
    print("\n\tid : %s \n\tp : %s\n\tsid : %s\n\tfh : %s\n\tnid : %s" % (m.id, m.path, m.sync_path_id, m.fhash, m.next_id))
    
def details(file_resolver):
    print('####main')
    kv = file_resolver.result()
    for k, v in kv.iteritems():
        print( "%s - %s\n" % (k, v))
    print("resolver end\n\n####")
    
    # 
    kv = file_resolver.first_parent.result()
    for k, v in kv.iteritems():
        print("%s - %s\n" % (k, v))
    print("resolver end\n")
