
class FileParts(object):
    chunk_size = 2*10**5
    data = None
    changed = False

    def __init__(self, data=None):
        self.load(data)

    def load(self, data):
        '''
            Populate fron json string
        '''
        self.changed = False if data else True
        self.data = ujson.load(data) if data else []
    
    def dump(self):
        self.changed = False
        return ujson.dump(self.data)
    
    def put(self, pos, adler_v, md5_v):
        '''
            Put data for next part
        '''
        if len(self.data) > pos:
            self.data = self.data[:pos]
        elif len(self.data) < pos:
            raise IndexError('Position not ready')
        self.data.append([adler_v, md5_v])

    def get_adler(self, pos):
        if len(self.data) > pos:
            return self.data[pos][0]
        return None

 

