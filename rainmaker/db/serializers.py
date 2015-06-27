
import ujson

class Serializer(object):
    data = None
    _changed = False
    verify_format = False
    _load = None
    _dump = None

    def __init__(self, data=None, on_change=None):
        self._on_change = on_change
        self.load(data)

    def load(self, data):
        '''
            Populate from json string
        '''
        self.changed = False if data else True
        data = ujson.loads(data) if data else []
        if self._load:
            self.data = []
            self._load(data)
        else:
            self.data = data

    def __verify_format(self):
        '''
            verify structure of loaded data
        '''
        raise NotImplementedError('Implemented by subclass')

    def dump(self):
        '''
            Dump changes and mark self as not changed
        '''
        self.changed = False
        if self._dump:
            return ujson.dumps(self._dump())
        return ujson.dumps(self.data)
    
    def clear(self):
        '''
            Wipe contents
        '''
        self.changed = True
        self.data = []

    def get(self, pos):
        '''
            Get value
        '''
        if len(self.data) > pos:
            return self.data[pos]
        return None

    @property
    def parts_count(self):
        '''
            Count parts
        '''
        return len(self)
    
    def __len__(self):
        '''
            Count parts
        '''
        return len(self.data)

    def __getitem__(self, i):
        '''
            We can be accessed like an array
        '''
        return self.data[i]

    @property
    def changed(self):
        '''
            Have we changed since:
            - last time dump was called
            - or init/load happened?
        '''
        return self._changed

    @changed.setter
    def changed(self, val):
        '''
            Mark change t/f
        '''
        if self._changed == False and val and self._on_change:
            self._on_change()
        self._changed = val 

class Versions(Serializer):
    
    def __init__(self, cls, data, sort, on_change):
        self.keys = []          # Array of keys to dump from object
        self._objects = None
        self.cls = cls
        self.sort_f = sort
        self.on_change = on_change
        super().__init__(data)
    
    @property
    def objects(self):
        '''
            Load Array of objects
        '''
        if self._objects is None:
            self._objects = [self.cls(**kwargs) for kwargs in self.data] if self.data else [] 
            self._objects = sorted(self._objects, key=self.sort_f)
        return self._objects
    
    def __getitem__(self, i):
        '''
            We can be accessed like an array
        '''
        return self.objects[i]

    def add(self, kwargs):
        '''
            Add version to array
        '''
        self.changed = True
        self.objects.insert(0, self.cls(**kwargs))
        self.data.insert(0, kwargs)

    def clear(self):
        self.changed = True
        self._objects = None
        self.data = []

class FilePiece():
    
    def __init__(self, pmd5, padler, poffset, plen):
        self.pmd5 = pmd5
        self.padler = padler
        self.poffset = poffset
        self.plen = plen

    def dump(self):
        return [self.pmd5, self.padler, self.poffset, self.plen]

class NeededPiece(FilePiece):
    
    def __init__(self, pmd5, padler, poffset, plen, pdone):
        self.pdone = pdone
        super().__init__(pmd5, padler, poffset, plen)

    def dump(self):
        return [self.pmd5, self.padler, self.poffset, self.plen, self.pdone]

class FileParts(Serializer):
    chunk_size = 2*10**5

    IDX_ADLER = 0
    IDX_MD5 = 1

    def __init__(self, data=None, on_change=None):
        super().__init__(data, on_change)
 
    def put(self, pmd5, padler, poffset, plen):
        '''
            Put data for next part
        '''
        self.changed = True
        if len(self.data) > pos:
            self.data = self.data[:pos]
        elif len(self.data) < pos:
            raise IndexError('Position not ready')
        fp = FilePiece(pmd5, padler, poffset, plen)
        self.data.append([adler_v, md5_v])
    
    def _load(self, data):
        for x in data:
            self.data.append(FilePiece(*x))

    def get_adler(self, pos):
        if len(self.data) > pos:
            return self.data[pos].padler
        return None
   
    def from_host_file(self, host_file):
        '''
            Import settings from host_file
        '''
        self.load(host_file.file_parts.data)
        self._complete = None

from rainmaker.file_system import hash_chunk

class NeededParts(Serializer):
    '''
        An Array of parts needed for download
    '''
    
    chunk_size = FileParts.chunk_size
    
    _complete = None
    _num_incomplete = 0

    @classmethod
    def from_file_parts(klass, file_parts):
        '''
            Import settings from host_file
        '''
        nparts = klass()
        data = file_parts.data
        for args in data:
            file_piece = NeededPiece(*args)
            nparts._append(file_piece)
        return nparts

    def __init__(self, data=None, on_change=None):
        super().__init__(data, on_change)
        self.__count_incomplete__()
    
    def __count_incomplete__(self):
        '''
            Count number of incomplete chunks
        '''
        if len(self.data) == 0:
            return
        self._num_incomplete = 0  
        for fpiece in self.data:
            if fpiece.pdone == False:
                self._num_incomplete += 1  
    
    def _load(self, data):
        for args in data:
            self._append(*args)
    
    def _dump(self):
        return [x.dump() for x in self.data]

    def _append(self, *args):
        '''
            Add needed chunk
        '''
        fpiece = NeededPiece(*args)
        self.data.append(fpiece)
        if not fpiece.pdone:
            self._num_incomplete += 1
        self.changed = True

    def yield_chunk(self, pos, chunk):
        '''
            - validate chunk
            - mark  as completed
        '''
        try:
            fpiece = self.data[pos]
        except IndexError as e:
            yield 'We don\'t need that part, index error.'
            return
        except TypeError as e:
            yield "List indecies must be Integer: %s" % pos
            return
        if fpiece.pdone == True:
            yield 'We already have that part'
            return
        if fpiece.plen != len(chunk):
            yield 'Part length mismatch'
            return
        if hash_chunk(chunk) != fpiece.pmd5:
            yield 'Part hash mismatch'
            return

        yield None

        # we only get this far if write went ok
        self.data[pos].pdone = True
        self._num_incomplete -= 1
        self.changed = True

    @property
    def complete(self):
        '''
            Check to see if all parts are complete
        '''
        return self._num_incomplete == 0
