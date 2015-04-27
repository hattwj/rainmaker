from nose.tools import assert_raises

from rainmaker.db.serializers import FileParts

def test_file_parts_serializer_can_put_and_get():
    fp = FileParts()
    fp.put(0, 12345, 67890)
    assert fp.get_adler(0) == 12345
    assert fp.get_adler(1) == None 
    assert_raises(IndexError, fp.put, 3, 123, 456)
    fp.put(1, 12345, 67890)
    fp.put(2, 12345, 67890)
    assert fp.get_adler(2) == 12345
    fp.put(0, 12345, 67890)
    assert fp.get_adler(2) == None
    assert_raises(IndexError, fp.put, 2, 12345, 456)


