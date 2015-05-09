
import ujson

class Serializer(object):
    data = None
    _changed = False
    
    def __init__(self, data=None, on_change=None):
        self._on_change = on_change
        self.load(data)

    def load(self, data):
        '''
            Populate fron json string
        '''
        self.changed = False if data else True
        self.data = ujson.loads(data) if data else []
    
    def dump(self):
        self.changed = False
        return ujson.dumps(self.data)
    
    def get(self, pos):
        if len(self.data) > pos:
            return self.data[pos]
        return None

    @property
    def parts_count(self):
        return len(self)
    
    def __len__(self):
        return len(self.data)

    @property
    def changed(self):
        return self._changed

    @changed.setter
    def changed(self, val):
        if self._changed == False and val and self._on_change:
            self._on_change()
        self._changed = val 

class Versions(Serializer):
    
    def __init__(self, cls, data, sort, on_change):
        self.keys = []
        self._objects = []
        self.cls = cls
        self.sort_f = sort
        self.on_change = on_change
        super(Versions, self).__init__(data)

    def load_objects(self, data):
        '''
            Load Array of objects
        '''
        self._objects = [self.cls(**kwargs) for kwargs in ujson.loads(data)] if data else [] 
        self.sort()

    def sort(self):
        self._objects = sorted(self._objects, key=self.sort_f)

    def dump(self):
        '''
            Dump state to string
        '''
        result = [rec.to_dict(*self.keys) for rec in self.data]
        self.changed = False
        return result

    def add(self, args):
        '''
            Add version to array
        '''
        self.changed = True
        self._objects.insert(0, self.cls(**args)) 

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
