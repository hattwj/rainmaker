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
from sqlalchemy.pool import StaticPool

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

def __inc_version__(context):
    ver = context.current_parameters['next_ver']
    return 0 if ver is None else ver + 1

file_params = ['id', 'rel_path', 'file_hash', 'file_size', 
    'does_exist', 'next_ver', 'next_id', 'is_dir']

class SyncFile(RainBase):
    """"""
    __tablename__ = 'sync_files'
    
    
    id = Column(Integer, primary_key=True)

    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)
    # backref adds sync_files to sync? test
    sync = relationship("Sync", backref=backref("sync_files", order_by=id))
    
    rel_path = Column(Text, nullable=False, index=True)
    file_hash = Column(Text, default='')
    file_size = Column(Integer, default=0)
    mtime = Column(Integer)
    ctime = Column(Integer)
    stime = Column(Integer, index=True, default=0)
    stime_start = Column(Integer, index=True, default=0)
    inode = Column(Integer)
    is_dir = Column(Boolean)
    does_exist = Column(Boolean)
    next_ver = Column(Integer, 
        default=0, nullable=False, onupdate=__inc_version__)
    next_id = Column(Integer)

    # backref adds sync_files to sync? test
    sync_parts = relationship('SyncPart', order_by='SyncPart.offset') 
    
    # attributes
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
        f = self.to_dict(*file_params)
        f['rid']=f.pop('id')
        return HostFile(**f)

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
    #ipv4 = Column(Text, nullable=False)
    device_name = Column(String(50))
    version = Column(String(50))
    pubkey = Column(String(150), nullable=False)
    #tcp_port = Column(Integer, nullable=False)
    #udp_port = Column(Integer, nullable=False)
    
    # set by session 
    sync_id = Column(Integer, ForeignKey("syncs.id"), index=True) 
    #sync = relationship(Sync, backref=backref("hosts", order_by=id )) 

    #@validates('tcp_port', 'udp_port')
    #def validates_port(self, key, val):
    #    assert val > 0
    #    assert val < 65535
    #    return val

class HostFile(RainBase):
    __tablename__ = 'host_files'
    __table_args__= (
        UniqueConstraint('host_id', 'rid'),    
    )
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
    file_hash = Column(Text, default='')
    file_size = Column(Integer, default=0)
    is_dir = Column(Boolean)
    does_exist = Column(Boolean)
    next_id = Column(Integer)
    next_ver = Column(Integer)
    
    def to_sync_file(self, sync_id):
        f = self.to_dict(*file_params)
        f.pop('id')
        f['sync_id'] = sync_id
        return SyncFile(**f)

class HostFileVersion(RainBase):
    ''' Store remote file version Information '''

    __tablename__ = 'host_file_versions'
    id = Column(Integer, primary_key=True)
    ver = Column(Integer, nullable=False)
    host_file_id = Column(Integer, ForeignKey("host_files.id"), index=True) 
    host_file = relationship("HostFile", backref=backref("versions", order_by=desc(ver) ))
    attrs_json = Column(Text, nullable=False)
    changes_json = Column(Text, nullable=False)

