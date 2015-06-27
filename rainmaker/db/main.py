import os

from sqlalchemy import create_engine, ForeignKey, UniqueConstraint, desc, event
from sqlalchemy import Column, Integer, Text, String, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, validates, sessionmaker, object_mapper
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.pool import StaticPool

import ujson

from rainmaker import utils
from rainmaker.db.serializers import FileParts, Versions, NeededParts
 
Base = declarative_base()

from contextlib import contextmanager
###
# Database Init
def init_db(location=':memory:', echo=False):
    engine = create_engine('sqlite:///%s' % location, 
            connect_args={'check_same_thread':False}, 
            #poolclass=StaticPool,
            echo=echo)
    DbConn = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all()

    @contextmanager
    def yield_conn():
        db = DbConn()
        try:
            yield db
        finally:
            db.close()
    DbConn.yield_conn = yield_conn
    return DbConn

class RainBase(Base):
    '''Default class for tables '''
    __abstract__ = True
    updated_at = Column(Integer, default=utils.time_now, onupdate=utils.time_now, nullable=False)
    created_at = Column(Integer, default=utils.time_now, nullable=False)

    def __repr__(self):
        return "{0}({1})".format(
            self.__class__.__name__,
            ', '.join(['{0}={1!r}'.format(*_) for _ in self.to_dict().items()]))

    def to_dict(self, *attrs):
        if not attrs:
            attrs = [c.name for c in self.__table__.columns]
        d = {name: getattr(self, name) for name in attrs}
        return d
    
    def to_json(self):
        return ujson.dumps(self.as_dict())

    def before_changes(self):
        ''' Get original attributes as dictionary '''
        return {c.name: get_was(self, c.name) for c in self.__table__.columns}

def get_was(record, key):
    ''' get values from record before any changes occurred '''
    hist = get_history(record, key)
    if hist.unchanged:
        return hist.unchanged[0]
    if hist.deleted:
        return hist.deleted[0]
    return None
    
class Sync(RainBase):
    __tablename__ = 'syncs'
    id = Column(Integer, primary_key=True)
    
    path = Column(Text, unique=True, nullable=False, index=True)
    stime_start = Column(Integer, index=True, default=0)
    stime = Column(Integer, index=True, default=0)
    tox_primary_blob = Column(Binary)    
    tox_sync_blob = Column(Binary) 

    def rel_path(self, val):
        assert val.startswith(self.path)
        assert len(val) > len(self.path)
        return val[len(self.path):][1:]

file_params = ['id', 'rel_path', 'file_hash', 'file_size', 
    'does_exist', 'is_dir', 'version']

class SyncFile(RainBase):
    """ Sync File """
    __table_args__= (
        UniqueConstraint('sync_id', 'rel_path'),    
    )
    ver_params = ['rel_path', 'file_hash', 'file_size', 'does_exist', 'is_dir',
            'version']
    __tablename__ = 'sync_files'
    id = Column(Integer, primary_key=True)
    # relative path
    rel_path = Column(Text, nullable=False, index=True)
    # 32 bit file hash
    file_hash = Column(Integer, default=0)
    # file size
    file_size = Column(Integer, default=0)
    # file part hashes
    fparts = Column(Text)
    # time modified
    mtime = Column(Integer)
    # time created
    ctime = Column(Integer)
    # time scan completed
    stime = Column(Integer, index=True, default=0)
    # time scan started
    stime_start = Column(Integer, index=True, default=0)
    # json version data
    ver_data = Column(Text)
    # file inode
    inode = Column(Integer)
    # is directory?
    is_dir = Column(Boolean, nullable=False)
    # not deleted?
    does_exist = Column(Boolean, nullable=False, index=True)
    
    version = Column(Integer, default=0, nullable=False)
    #next_id = Column(Integer)

    # Add relationships
    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)
    sync = relationship('Sync', backref=backref('sync_files', cascade='all, delete-orphan'))

    # Empty attributes for HostFile comparison
    cmp_ver = None
    cmp_id = None
    
    # temp val for holding full path
    _path = None
    
    @property
    def path(self):
        assert self.sync is not None
        assert self.rel_path is not None
        if self._path is None:
            self._path = os.path.join(self.sync.path, self.rel_path)
        return self._path
    
    @path.setter
    def path(self, val):
        assert self.sync is not None
        assert val.startswith(self.sync.path)
        self.rel_path = val[len(self.sync.path):][1:]
    
    def to_host_file(self):
        ''' Export self as host file '''
        f = self.to_dict(*file_params)
        f['rid']=f.pop('id')
        return HostFile(**f)
    
    __versions__ = None

    @property
    def vers(self):
        ''' read only copy of past versions '''
        if self.__versions__ is None:
            versions = Versions(SyncFile, data=self.ver_data,
                            sort=lambda ver: ver.version,
                            on_change=lambda: setattr(self, 'ver_data',  None))
            versions.keys = self.ver_params    
            self.__versions__ = versions
        return self.__versions__
    
    # Debug setter
    @vers.setter
    def vers(self, val):
        self.ver_data = None
        self.vers.clear()
        for ver in val:
            self.vers.add(ver)
        self.ver_data = self.vers.dump()
    

    __file_parts__ = None

    @property
    def file_parts(self):
        def _on_change():
            self.fparts = None
        if self.__file_parts__ is None:
            self.__file_parts__ = FileParts(data=self.fparts, on_change=_on_change)
        return self.__file_parts__

class ToxServer(RainBase):
    __tablename__ = 'tox_servers'
    id = Column(Integer, primary_key=True)
    ipv4 = Column(Text, nullable=False, unique=True)
    pubkey = Column(Text, nullable=False)
    port = Column(Integer, nullable=False)
    fails = Column(Integer, default=0, nullable=False)

    @validates('port')
    def validates_port(self, key, val):
        assert val > 0
        assert val < 65535
        return val

class Host(RainBase):
    __tablename__ = 'hosts'
    id = Column(Integer, primary_key=True)
    device_name = Column(String(50))
    version = Column(String(50))
    pubkey = Column(String(150), nullable=False)
    
    # fk 
    sync_id = Column(Integer, ForeignKey("syncs.id"), index=True) 
    
    # Add relationships
    sync = relationship('Sync', backref=backref('hosts', 
        cascade='all, delete-orphan'))

class HostFile(RainBase):
    __tablename__ = 'host_files'
    __table_args__= (
        UniqueConstraint('host_id', 'rid'),    
    )
    __versions__ = None
 
    # local primary key ( remote from owners perspective )
    id = Column(Integer, primary_key=True)

    host_id = Column(Integer, ForeignKey("hosts.id"), index=True, nullable=False) 
    host = relationship("Host", backref=backref('host_files', 
        cascade='all, delete-orphan'))
    
    # must have default values for sync_join view to work
    rid = Column(Integer, nullable=False)
    rel_path = Column(Text, nullable=False, index=True)
    fparts = Column(Text)
    file_hash = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    is_dir = Column(Boolean)
    does_exist = Column(Boolean)
    # json version data
    ver_data = Column(Text)
    version = Column(Integer, default=0, nullable=False)
    # sync_file_id of last comparison 
    cmp_id = Column(Integer)
    # sync_file.version of last comparison 
    cmp_ver = Column(Integer)

    # convert to sync_file
    def to_sync_file(self, sync_id):
        ''' Used for testing '''
        f = self.to_dict(*file_params)
        f.pop('id')
        f['sync_id'] = sync_id
        return SyncFile(**f)
  
    ## 
    # Must be called "vers"
    # some sort of setter/getter bug if we call this "versions"
    @property
    def vers(self):
        ''' read only copy of past versions '''
        if self.__versions__ is not None: 
            return self.__versions__
        if self.ver_data is None or len(self.ver_data) == 0:
            return []
        self.__versions__ = [HostFile(**ver) for ver in ujson.loads(self.ver_data)]
        self.__versions__.sort(key=lambda ver: ver.version)        
        return self.__versions__
    
    @vers.setter
    def vers(self, val):
        ''' Used for testing '''
        self.ver_data = ujson.dumps(val)
        versions = [HostFile(**ver) for ver in val]
        for v in versions:
            assert v.version is not None 
        self.__versions__ = versions

    __file_parts__ = None
    
    @property
    def file_parts(self):
        if self.__file_parts__ is None:
            self.__file_parts__ = FileParts(data=self.fparts, on_change=lambda: setattr(self, 'fparts', None))
        return self.__file_parts__

class Download(RainBase):
    '''
        Holds download status of resolution
    '''
    __tablename__ = 'downloads'
    __table_args__= (
        UniqueConstraint('sync_id', 'rel_path'),    
    )
    id = Column(Integer, primary_key=True)
    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)

    # fk 
    #resolution_id = Column(Integer, ForeignKey("resolutions.id"), index=True, unique=True)
    
    # path
    rel_path = Column(Text, nullable=False, index=True)
    # 32 bit file hash
    file_hash = Column(Integer, default=0)
    # file size
    file_size = Column(Integer, default=0)
    # is_dir
    is_dir = Column(Boolean)
    
    # download complete
    complete = Column(Boolean, default=False)

    # file part hashes
    nparts = Column(Text)

    @property
    def incoming_path(self):
        return self.path + '.part'

    __needed_parts__ = None
    @property
    def needed_parts(self):
        if self.__needed_parts__ is None:
            self.__needed_parts__ = NeededParts(self.nparts)
        return self.__needed_parts__
    
    # temp val for holding full path
    _path = None
    
    @property
    def path(self):
        assert self.sync is not None
        assert self.rel_path is not None
        if self._path is None:
            self._path = os.path.join(self.sync.path, self.rel_path)
        return self._path

    @property
    def is_complete(self):
        return self.needed_parts.complete
 
class Resolution(RainBase):
    '''
        Holds resolution status between sync_file and host_file
    '''
    # Resolution State Constants
    RES_ERROR       = 9 # Error during resolution
    CONFLICT_MINE   = 7 # Decided to keep mine
    CONFLICT_THEIRS = 6 # Decided to keep theirs
    CONFLICT        = 5 # Undecided conflict
    THEIRS_CHANGED  = 3 # Change to host_file
    MINE_CHANGED    = 2 # Change to sync_file
    NEW             = 0 # New file
    
    # File Status Constants
    DELETED         = 3 
    MOVED           = 2
    MODIFIED        = 1
    CREATED         = 0
    NO_CHANGE       = -1 # Nothing changed


    __tablename__ = 'resolutions'
    id = Column(Integer, primary_key=True) 
    # Add relationships
    #download = relationship('Download', uselist=False, backref='resolution')

    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)
    sync = relationship('Sync', backref=backref('resolutions', cascade='all, delete-orphan'))
    
    host_id = Column(Integer, ForeignKey("hosts.id"), index=True, nullable=False) 
    host = relationship("Host", backref=backref('resolutions', 
        cascade='all, delete-orphan'))

    sync_file_id = Column(Integer, ForeignKey("sync_files.id"), index=True)
    sync_file_ver = Column(Integer)
    sync_file = relationship('SyncFile', backref=backref('resolutions'))
    
    host_file_id = Column(Integer, ForeignKey("host_files.id"), index=True)
    host_file_ver = Column(Integer)
    host_file = relationship('HostFile', backref=backref('resolutions'))
    
    state = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)

