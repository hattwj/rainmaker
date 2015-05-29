from nose.tools import assert_raises

from rainmaker.db.serializers import FileParts, NeededParts
from rainmaker.tests.factory_helper import Sync, Host, HostFile 
from rainmaker.db.main import init_db

def test_file_parts_can_put_get_dump_load():
    fp = FileParts()
    fp.put(0, 12345, 67890)
    assert fp.get_adler(0) == 12345
    assert fp.get_adler(1) == None 
    assert_raises(IndexError, fp.put, 3, 123, 456)
    fp.put(1, 12345, 67890)
    fp.put(2, 123456, 67890)
    assert fp.get_adler(2) == 123456
    fp.put(0, 12345, 67890)
    assert fp.get_adler(2) == None
    assert_raises(IndexError, fp.put, 2, 12345, 456)
    assert fp.data == FileParts(data=fp.dump()).data
    assert len(fp.data) == 1

def test_needed_parts_can_dump_load():
    # Setup
    sync = Sync(fake=True)
    host = Host(sync, 1)
    host_file = HostFile(host, 1, is_dir=False) 
    np = NeededParts()
    
    # Assert able to import
    np.from_host_file(host_file)
    assert np.parts_count > 0
    assert np.parts_count == host_file.file_parts.parts_count
    # Assert can dump/load
    assert np.data == NeededParts(data=np.dump()).data
    
def test_needed_parts_can_copy_host_file():
    # Setup
    sync = Sync(fake=True)
    host = Host(sync, 1)
    host_file = HostFile(host, 1, is_dir=False)
    
    # assert empty
    np = NeededParts()
    assert np.parts_count == 0
    
    # Assert able to import
    np.from_host_file(host_file)
    assert np.parts_count > 0
    assert np.parts_count == host_file.file_parts.parts_count
        
    # Assert can be complete
    for pos in np.parts_range:
        assert np.is_part_complete(pos) == False
        np.part_received(pos)
    # check complete 
    assert np.complete == True

def test_needed_parts_can_copy_host_dir():
    # Setup
    sync = Sync(fake=True)
    host = Host(sync, 1)
    host_file = HostFile(host, 1, is_dir=True)
    
    # assert empty
    np = NeededParts()
    assert np.parts_count == 0
    
    # Assert able to import
    np.from_host_file(host_file)
    assert np.parts_count == 0
    assert np.parts_count == host_file.file_parts.parts_count
    
def test_empty_needed_parts_is_complete():
    # assert empty
    np = NeededParts()
    assert np.parts_count == 0
    assert np.complete == True    

