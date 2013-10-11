from . common import *

class Base(DBObject):
    #Column names
    columns = None

    #Original values
    data_was = None

    # Super class
    @classmethod
    def find_many(klass, arr=None, col='id'):
        if not arr:
            return []
        where_ids = []
        where = ''
        for val in arr:
            where_ids.append( val )
            if where == '':
                where = "%s = ?" % col
            else:
                where += ' OR %s = ?' % col
        where_ids.insert(0, where)
        return klass.find(where=where_ids)

    # Possibly migrate into super_class
    def __init__(self, **kwargs):
        DBObject.__init__(self, **kwargs)
        ''' Save original values '''
        self._do_data_was()

    def _do_data_was(self):
        self.data_was = {}
        for k in self.columns:
            self.data_was[k] = getattr(self, k)

    # Super class
    def changed(self, cols=None):
        if cols == None:
            cols=self.data_was.keys()
        
        for k in cols:
            if getattr(self,k) != self.data_was[k]:
                return True
        return False

