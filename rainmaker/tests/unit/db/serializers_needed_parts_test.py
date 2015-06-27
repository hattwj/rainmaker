import ujson
from rainmaker.db.serializers import NeededParts, NeededPiece, FileParts
from rainmaker.file_system import hash_chunk

def gen_piece_args(chunk=b''):
    return [hash_chunk(chunk), '', 0, len(chunk), False]

def test_needed_parts_can_load():
    # Setup
    pa = gen_piece_args()
    np = NeededParts(ujson.dumps([pa]))
    # Assert able to import
    assert np.parts_count == 1

def test_needed_parts_can_dump():
    # Setup
    pa = gen_piece_args()
    np = NeededParts(ujson.dumps([pa]))
    # Assert can dump/load
    assert np.dump() == NeededParts(data=np.dump()).dump()

def test_needed_parts_can_yield_valid_chunk():
    test_str = b'test_string'
    # Setup
    pa = gen_piece_args(test_str)
    np = NeededParts(ujson.dumps([pa]))

    did_yield = False
    for err in np.yield_chunk(0, test_str):
        did_yield = True
        assert err is None
    assert did_yield

def test_needed_parts_can_yield_chunk_errors():
    test_str = b'test_string'
    # Setup
    pa = gen_piece_args(test_str)
    np = NeededParts(ujson.dumps([pa]))

    did_yield = False
    for err in np.yield_chunk(0, b'bad_chunk'):
        did_yield = True
        assert err is not None
    assert did_yield
    
    # index out of bounds
    did_yield = False
    for err in np.yield_chunk(1234, test_str):
        did_yield = True
        assert err is not None
    assert did_yield
    
    did_yield = False
    for err in np.yield_chunk('bad idx', test_str):
        did_yield = True
        assert err is not None
    assert did_yield
    
    did_yield = False
    for err in np.yield_chunk(0, 'not a byte array'):
        did_yield = True
        assert err is not None
    assert did_yield

def test_can_import_from_file_parts():
    fp = FileParts()
    np = NeededParts.from_file_parts(fp)
    assert len(np.data) == 0

