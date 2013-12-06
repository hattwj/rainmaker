from . common import *
from rainmaker_app.lib.lib_hash import md5Checksum as checksum

class MyFile(Base):

    BELONGSTO = ['sync_path']
    HASMANY = ['file_versions']
    
    BEFORE_CREATE = ['set_created_at','set_updated_at']
    BEFORE_SAVE = ['set_updated_at','create_new_version']
    FIRST_INIT = ['init_state']

    #State Constants
    ERROR      = 999
    CONFLICT   = 888
    DELETED    = 4
    MODIFIED   = 3
    MOVED      = 2
    NO_CHANGE  = 1
    NEW = 0
    
    CREATE_NEW_AND_SAVE = [MODIFIED, MOVED]

    #Defaults
    state = NEW
    mtime = None
    ctime = None
    path = None
    inode = None
    fhash = None
    my_file_id = None
    is_dir = False
    size = 0
    id = None

    #Column names
    ATTR_ACCESSIBLE = ['size', 'fhash', 'inode', 'mtime', 'ctime', 'path', 'state', 'is_dir' ]
    fstat_columns = ['inode', 'mtime', 'ctime' ]
    
    
    @classmethod
    @defer.inlineCallbacks
    def active_files(klass, sync_path_id): 
        my_files = yield klass.find(where=[
            'next_id IS NULL AND state != ? AND sync_path_id = ?',
            klass.DELETED,
            sync_path_id
        ], orderby='path,state,fhash,is_dir')
        defer.returnValue( my_files )
    
    @classmethod
    @defer.inlineCallbacks
    def active_files_since(klass, sync_path_id, int_date ): 
        my_files = yield klass.find(where=[
            'next_id IS NULL AND state != ? AND sync_path_id = ? AND updated_at > ?',
            klass.DELETED,
            sync_path_id,
            int_date
        ], orderby='path,state,fhash,is_dir')
        defer.returnValue( my_files )
                    
    def init_state(self):
        ''' only runs on new records '''
        if self.state == self.NEW:
            if self.fhash != None or self.is_dir == True:
                self.state = self.NO_CHANGE
    
    def has_fstat_changed(self):
        ''' Check for file changes '''
        f=open( self.path, 'rb' )
        finfo = os.fstat(f.fileno()) 
        f.close()
        self.size = finfo.st_size
        self.inode = finfo.st_ino
        self.mtime = finfo.st_mtime
        self.ctime = finfo.st_ctime 
        return self.changed(self.fstat_columns)
    
    # Super class
    def changed(self, cols=None):
        if cols == None:
            cols=self.data_was.keys()
        
        for k in cols:
            if getattr(self,k) != self.data_was[k]:
                return True
        return False

    @defer.inlineCallbacks 
    def create_new_version(self):

        # shouldn't use state for modified?
        if self.state == self.MODIFIED:
            self.state = self.NO_CHANGE
        
        # save old version
        if self.data_was['id'] and self.changed() and self.next_id == None:
            old_file = MyFile(**self.data_was)
            old_file.id = None
            old_file.next_id = self.id
            gg = yield old_file.save()
        # change stored values
        self._do_data_was()
         
    @defer.inlineCallbacks
    def delete_file(self):
        ''' delete file '''
        self.state = MyFile.DELETED
        yield self.save()
        defer.returnValue( 'not implemented')

    def is_new(self):
        ''' check if record is new '''
        return self.state == self.NEW
    
    def is_error(self):
        ''' check if record is new '''
        return self.state == self.ERROR

    def is_no_change(self):
        ''' check if record is new '''
        return self.state == self.NO_CHANGE
        
    def is_stale(self):
        ''' check if record is stale '''
        if self.state in self.CREATE_NEW_AND_SAVE:
            return True
        return False
 
    def is_deleted(self):
        return self.state == self.DELETED

    def reset(self):
        '''
        Reset values
        '''
        for k, v in self.data_was.iteritems():
            setattr(self,k,v)
        return True

    def scan(self):
        '''
        create or update file info of path
        check for changes
        '''
        
        def _scan(self):
            if self.state == self.DELETED:
                self.state = self.MODIFIED

            if  os.path.isdir( self.path ):
                self.is_dir = True
                return 
            
            has_changed = self.has_fstat_changed()
                    
            if self.is_new() or has_changed:
                self.fhash = checksum( self.path )
            
            if has_changed and self.is_new() == False:
                self.state = self.MODIFIED
        
        self.scanned_at = int( round( time() * 1000 ) )
        try:
            _scan(self)
        except:
            if not os.path.exists( self.path ):
                self.state = self.DELETED
            else:
                self,state = self.ERROR

@defer.inlineCallbacks
def must_be_unique(my_file):
    ''' Require that path, sync_path_id, next_id combos are unique '''
    if my_file.next_id:
        my_files = yield MyFile.find(where=[
            'sync_path_id = ? AND path = ? AND next_id = ?',
            my_file.sync_path_id,
            my_file.path,
            my_file.next_id
        ])
    else:
        my_files = yield MyFile.find(where=[
            'sync_path_id = ? AND path = ? AND next_id IS NULL',
            my_file.sync_path_id,
            my_file.path
        ])
    if my_files:
        my_file.errors.add('path','already exists')

MyFile.addValidator(must_be_unique)
    
