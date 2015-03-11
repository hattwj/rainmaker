import os
import yaml
import pprint
pp = pprint.PrettyPrinter(indent=2, depth=6).pprint

from rainmaker.tests import test_helper
from rainmaker.db.main import init_db
from rainmaker.db import views
from rainmaker.sync_manager.resolver import FileResolver

raw_data = test_helper.load(os.path.join('fixtures', 
    'unit', 'sync_manager', 'resolver_test.yml'))
test_data = yaml.safe_load(raw_data)

# Test Preparation 
def setup():
    test_helper.clean_temp_dir()

def teardown():
    pass
        
def test_resolve_syncs():
    # def resolve_against(self, sync_paths_arr):
    expected = test_data['resolve_syncs']['expected']
    resolvers = FileResolver.resolve_syncs( [1,2] )
    for s in resolvers:
        r = s.last_child
        result = [ sorted([s.id for s in r.related_files]), \
            sorted([s.id for s in r.peer_files]), r.state ]
        assert result in expected

# Tests
def test_deleted_no_conflict():
    Run('deleted_no_conflict').expect_state(FileResolver.DELETED)

def test_modified_no_conflict():
    Run('modified_no_conflict').expect_state(FileResolver.MODIFIED)

def test_moved_no_conflict():
    Run('moved_no_conflict').expect_state(FileResolver.MOVED)

def test_new_no_conflict():
    Run('new_no_conflict').expect_state(FileResolver.NEW)

def test_simple_conflict():
    Run('simple_conflict').expect_state(FileResolver.CONFLICT)

def test_renamed_conflict():
    Run('renamed_conflict').expect_state(FileResolver.CONFLICT)

class Run(object):
    def __init__(self, test_name):
        session = init_db()
        test_helper.load_fixture(session, test_name, test_data)
        self.session = session

    def expect_state(self, expected_state):
        l_files, r_files = views.sync_diff(self.session, 1, 1)
        my_files = l_files + r_files
        pp(my_files)
        # process all new files
        while len(my_files) > 0:
            my_file = my_files.pop()
            file_resolver = FileResolver(my_file)
            file_resolver.resolve_against(my_files)
            pp(file_resolver.result())
            print(file_resolver.state)
            assert file_resolver.state == expected_state 
            # prep for next round
            my_files = file_resolver.unrelated_files

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
