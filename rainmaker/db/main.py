'''
    Initialize database
    Run migrations
    Configure models
'''
import os

from sqlalchemy import create_engine, ForeignKey, UniqueConstraint, desc, event
from sqlalchemy import Column, Integer, Text, String, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, validates, sessionmaker, object_mapper
from sqlalchemy.orm.attributes import get_history
#from sqlalchemy.pool import StaticPool

import ujson

from rainmaker import utils

 
Base = declarative_base()
engine = None
session = None

###
# Database Init
def init_db(location=':memory:', echo=False):
    global engine
    global session
    engine = create_engine('sqlite:///%s' % location, 
            #connect_args={'check_same_thread':False}, 
            #poolclass=StaticPool,
            echo=echo)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.bind = engine
    Base.metadata.create_all()
    return session

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
    hosts = relationship('Host', backref="sync") 

    def rel_path(self, val):
        assert val.startswith(self.path)
        assert len(val) > len(self.path)
        return val[len(self.path):][1:]

file_params = ['id', 'rel_path', 'file_hash', 'file_size', 
    'does_exist', 'is_dir']

class SyncFile(RainBase):
    """ Sync File """
    __versions__ = None
    __table_args__= (
        UniqueConstraint('sync_id', 'rel_path'),    
    )

    __tablename__ = 'sync_files'
    id = Column(Integer, primary_key=True)
    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)
    # backref adds sync_files to sync? test
    sync = relationship("Sync", backref=backref("sync_files", order_by=id))
    # relative path
    rel_path = Column(Text, nullable=False, index=True)
    # 32 bit file hash
    file_hash = Column(Integer, default=0)
    # file size
    file_size = Column(Integer, default=0)
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
    is_dir = Column(Boolean)
    # not deleted?
    does_exist = Column(Boolean, index=True)
    
    version = Column(Integer, default=0, nullable=False)
    #next_id = Column(Integer)

    # backref adds sync_files to sync? test
    sync_parts = relationship('SyncPart', order_by='SyncPart.offset') 
    
    # temp val for holding full path
    _path = None
    
    # Empty attributes for HostFile comparison
    cmp_ver = None
    cmp_id = None

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

    @property
    def vers(self):
        ''' read only copy of past versions '''
        if self.__versions__ is not None: 
            return self.__versions__
        if self.ver_data is None or len(self.ver_data) == 0:
            return []
        self.__versions__ = [SyncFile(**ver) for ver in ujson.loads(self.ver_data)]
        self.__versions__.sort(key=lambda ver: ver.version)
        return self.__versions__
    
    # Debug setter
    @vers.setter
    def vers(self, val):
        self.ver_data = ujson.dumps(val)
        versions = [SyncFile(**ver) for ver in val]
        for v in versions:
            assert v.version is not None 
        self.__versions__ = versions
         

# standard decorator style
@event.listens_for(SyncFile, 'before_update')
def receive_before_update(mapper, connection, target):
    "listen for the 'before_update' event"
    do_versioning(target)

def do_versioning(target):
    target.version += 1
    data = [target.before_changes()]
    if target.ver_data is not None:
        data.append(ujson.dumps(target.ver_data))
    target.ver_data = ujson.dumps(data)

class SyncPart(RainBase):
    __tablename__ = 'sync_parts'
    __table_args__ = (
        UniqueConstraint('sync_file_id', 'offset'),
    )

    id = Column(Integer, primary_key=True)
    offset = Column(Integer, nullable=False, index=True)
    part_len = Column(Integer, nullable=False, index=True)
    part_hash = Column(String(32), nullable=False)
    rolling_hash = Column(Integer, nullable=False)
    sync_file_id = Column(Integer, ForeignKey("sync_files.id"), nullable=False, index=True)

class SyncFileVersion(RainBase):
    __tablename__ = 'sync_file_versions'
    id = Column(Integer, primary_key=True)
    ver = Column(Integer, nullable=False)
    sync_file_id = Column(Integer, ForeignKey("sync_files.id"), index=True) 
    sync_file = relationship("SyncFile", backref=backref("versions", order_by=desc(ver) ))
    changes_json = Column(Text, nullable=False)
    attrs_json = Column(Text, nullable=False)

class ToxServer(RainBase):
    __tablename__ = 'tox_servers'
    id = Column(Integer, primary_key=True)
    ipv4 = Column(Text, nullable=False)
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
    
    # set by session 
    sync_id = Column(Integer, ForeignKey("syncs.id"), index=True) 

'''
    ver_data = string
    versions = arr of 
'''

class HostFile(RainBase):
    __tablename__ = 'host_files'
    __table_args__= (
        UniqueConstraint('host_id', 'rid'),    
    )
    __versions__ = None
 
    # local primary key ( remote from owners perspective )
    id = Column(Integer, primary_key=True)

    host_id = Column(Integer, ForeignKey("hosts.id"), index=True, nullable=False) 
    host = relationship("Host", backref=backref("host_files", order_by=id ))
    
    # mapping for after file comparison
    sync_file_id = Column(Integer, ForeignKey("sync_files.id"), index=True) 
    sync_file = relationship("SyncFile", backref=backref("host_files", order_by=id))
    # must have default values for sync_join view to work
    rid = Column(Integer, nullable=False)
    rel_path = Column(Text, nullable=False)
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
        f = self.to_dict(*file_params)
        f.pop('id')
        f['sync_id'] = sync_id
        return SyncFile(**f)
   
    # some sort of setter/getter bug if we call this versions
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
        self.ver_data = ujson.dumps(val)
        versions = [HostFile(**ver) for ver in val]
        for v in versions:
            assert v.version is not None 
        self.__versions__ = versions

class HostFileVersion(RainBase):
    ''' Store remote file version Information '''

    __tablename__ = 'host_file_versions'
    id = Column(Integer, primary_key=True)
    ver = Column(Integer, nullable=False)
    host_file_id = Column(Integer, ForeignKey("host_files.id"), index=True) 
    host_file = relationship("HostFile", backref=backref("versions", order_by=desc(ver) ))
    attrs_json = Column(Text, nullable=False)
    changes_json = Column(Text, nullable=False)

