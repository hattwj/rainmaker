import json
from . common import *

class Base(DBObject):
    #Column names
    columns = None

    # instantiated by sub class for safe_init
    safe_columns = None

    #Original values
    data_was = None

    @classmethod
    def safe_init(klass, **kwargs):
        ''' mass assignment protection '''
        new_klass = klass()
        new_klass.safe_update( kwargs )
        return new_klass

    
    def safe_update(self, opts):
        if not self.safe_columns:
            raise NoSafeColsError
        keys = opts.keys()
        for k in self.safe_columns:
            if k in keys:
                setattr(self, k, opts[k])

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
    
    @property
    def serialized_data(self):
        result = {}
        for k in self.columns:
            result[k] = getattr(self, k)
        return result 

    def to_json(self):
        return json.dumps( self.serialized_data )
   
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

class NoSafeColsError(Exception):
    ''' no safe cols defined for class'''
    pass
