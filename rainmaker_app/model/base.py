import json
from . common import *
from rainmaker_app.lib.util import ExportArray, time_now

class Base(DBObject):
    #Column names
    #columns = None
    sticky_table = False # allow console db clear
    BEFORE_CREATE = None# Before Created, but after validation
    BEFORE_SAVE = None  # Before Saved, but after validation
    AFTER_CREATE = None
    FIRST_INIT = None   # Only for new records
    AFTER_INIT = None   # Every time a record in instantiated

    # instantiated by sub class for safe_init
    ATTR_ACCESSIBLE = None
    ATTR_DEFAULTS = None

    #Original values
    data_was = None
   
    def __init__(self, **kwargs):
        # Create attr_accessible attributes first
        # or init will wipe them
        self._do_attr_accessible(kwargs)
        DBObject.__init__(self, **kwargs)
        # Save original values
        self._do_data_was()
        self.__run_hooks__(self.AFTER_INIT)
        if self.new_record:
            self.afterInit()

    @property 
    def new_record(self):
        ''' is this a new record? '''
        return self.id == None

    def afterInit(self): 
        ''' Only for new records '''
        if not self.new_record:
            return
        self.__run_hooks__(self.FIRST_INIT)
        self.FIRST_INIT = None

    def beforeCreate(self):
        return self.__run_hooks__(self.BEFORE_CREATE)
    
    def beforeSave(self):
        return self.__run_hooks__(self.BEFORE_SAVE)

    def afterCreate(self):
        return self.__run_hooks__(self.AFTER_CREATE)

    @defer.inlineCallbacks
    def __run_hooks__(self, funcs):
        ''' run the included list of functions '''
        if not funcs:
            return
        for func_name in funcs:
            # Get Function which may be a deferred
            func = getattr(self,func_name)
            
            # Call a maybe deferred
            success = yield defer.maybeDeferred(func)

            # Bail if it failed
            if success == False:
                defer.returnValue(False)
                return
        defer.returnValue( True )

    def set_updated_at(self):
        ''' Set updated at '''
        self.updated_at = self.time_now()
    
    def set_created_at(self):
        ''' Set created at '''
        self.created_at = self.time_now() 
        self.updated_at = self.time_now()
    
    def time_now(self):
        return time_now()  

    @classmethod
    def safe_init(klass, **kwargs):
        ''' mass assignment protection '''
        new_klass = klass()
        new_klass.safe_update( kwargs )
        return new_klass
    
    def safe_update(self, opts):
        if not self.ATTR_ACCESSIBLE:
            raise NoSafeColsError
        keys = opts.keys()
        for k in self.ATTR_ACCESSIBLE:
            if k in keys:
                setattr(self, k, opts[k])
   
    # Super class
    @classmethod
    def find_many(klass, q_vals=None, col='id', where=None):
        if not where:
            where = []
        # Create giant OR sql statement
        q_str = ' OR '.join( ['%s = ?' % col for val in q_vals] )
        
        # Wrap statement in an AND statement if where was included
        if where:
            q_str = '%s AND (%s)' % (where[0], q_str)
            q_vals = where[1:] + q_vals
        return klass.find(where=[q_str] + q_vals)
    
    @property
    def serialized_data(self):
        result = {}
        for k in self.ATTR_ACCESSIBLE:
            result[k] = getattr(self, k)
        return result 

    def to_json(self):
        return json.dumps( self.serialized_data )
 
    def to_dict(self):
        return self.serialized_data

    def _do_attr_accessible(self, kwargs):
        """ Create all attr accessible attributes """
        if self.ATTR_ACCESSIBLE:
            for k in self.ATTR_ACCESSIBLE:
                if k in kwargs.keys():
                    v = kwargs.pop(k)
                    setattr(self, k, v)

    def _do_data_was(self):
        ''' record the old value of the data so we can see if anything changes '''
        self.data_was = {}
        for k in self.columns:
            if not hasattr(self, k):
                setattr(self, k, None)
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
