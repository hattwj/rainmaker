
import ujson

class Serializer(object):
    data = None
    _changed = False
    
    def __init__(self, data=None, on_change=None):
        self._on_change = on_change
        self.load(data)

    def load(self, data):
        '''
            Populate from json string
        '''
        self.changed = False if data else True
        self.data = ujson.loads(data) if data else []
    
    def dump(self):
        '''
            Dump changes and mark self as not changed
        '''
        self.changed = False
        return ujson.dumps(self.data)
    
    def clear(self):
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
            Have we changed?
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
        super(Versions, self).__init__(data)
    
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

class FileParts(Serializer):
    chunk_size = 2*10**5
    def __init__(self, **kwargs):
        super(FileParts, self).__init__(**kwargs)
 
    def put(self, pos, adler_v, md5_v):
        '''
            Put data for next part
        '''
        self.changed = True
        if len(self.data) > pos:
            self.data = self.data[:pos]
        elif len(self.data) < pos:
            raise IndexError('Position not ready')
        self.data.append([adler_v, md5_v])

    def get_adler(self, pos):
        if len(self.data) > pos:
            return self.data[pos][0]
        return None
    
class NeededParts(Serializer):
    '''
        An Array of parts needed for download
    '''
 
    def __init__(self, **kwargs):
        super(NeededParts, self).__init__(**kwargs)
        self._complete = None

    def from_host_file(self, host_file):
        '''
            Import settings from host_file
        '''
        data = host_file.file_parts.data
        self.data = [False for x in data]
        self.changed = True
        self._complete = None

    def part_received(self, pos):
        '''
            Mark one part as completed
        '''
        self.data[pos] = True
        self.changed = True
        self._complete = None
    
    def is_part_complete(self, pos):
        '''
            check to see if this part is complete
        '''
        return self.data[pos]

    @property
    def parts_range(self):
        return range(0, self.parts_count)

    @property
    def complete(self):
        '''
            Check to see if all parts are complete
        '''
        if self._complete is not None:
            return self._complete
        self._complete = not (False in self.data)
        return self._complete
