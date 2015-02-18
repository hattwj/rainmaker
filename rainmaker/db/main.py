'''
    Initialize database
    Run migrations
    Configure models
'''
import os

from sqlalchemy import create_engine, ForeignKey, UniqueConstraint, desc
from sqlalchemy import Column, Integer, Text, String, Binary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, validates, sessionmaker, object_mapper

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
    engine = create_engine('sqlite:///%s' % location, echo=echo)
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
        mapper = object_mapper(self)
        items = [(p.key, getattr(self, p.key))
            for p in [
                    mapper.get_property_by_column(c) for c in mapper.primary_key]]
        return "{0}({1})".format(
            self.__class__.__name__,
            ', '.join(['{0}={1!r}'.format(*_) for _ in items]))


    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def as_json(self):
        return ujson.dumps(self.as_dict())

class Sync(RainBase):
    __tablename__ = 'syncs'
    id = Column(Integer, primary_key=True)
    
    path = Column(Text, unique=True, nullable=False, index=True)
    last_ver_id = Column(Integer)
    tox_primary_blob = Column(Binary)    
    tox_sync_blob = Column(Binary)    
    
    #@validates('xroot')
    #def validate_root(self, key, val):
    #    assert os.path.isdir(val) == True 
    
    def rel_path(self, val):
        print('sync_rel: ', val, 'to: ', val[len(self.path):][1:])
        assert val.startswith(self.path)
        assert len(val) > len(self.path)
        return val[len(self.path):][1:]

def __inc_version__(context):
    ver = context.current_parameters['next_ver']
    return 0 if ver is None else ver + 1

class SyncFile(RainBase):
    """"""
    __tablename__ = 'sync_files'
    
    
    id = Column(Integer, primary_key=True)

    sync_id = Column(Integer, ForeignKey("syncs.id"), nullable=False, index=True)
    # backref adds sync_files to sync? test
    sync = relationship("Sync", backref=backref("sync_files", order_by=id))
    
    rel_path = Column(Text, nullable=False, index=True)
    file_hash = Column(Text)
    file_size = Column(Integer)
    file_parts = Column(Text)
    mtime = Column(Integer)
    ctime = Column(Integer)
    stime = Column(Integer)
    inode = Column(Integer)
    is_dir = Column(Boolean)
    does_exist = Column(Boolean)
    next_ver = Column(Integer, 
        default=0, nullable=False, onupdate=__inc_version__)
    
    # attributes
    _path = None

    @property
    def path(self):
        assert self.sync is not None
        assert self.rel_path is not None
        if self._path is None:
            self._path = os.path.join(self.sync.path, self.rel_path)
        print('spath: ', self.sync.path, 'rel: ', self.rel_path, '_path: ',self._path)
        return self._path
    
    @path.setter
    def path(self, val):
        assert self.sync is not None
        assert val.startswith(self.sync.path)
        self.rel_path = val[len(self.sync.path):][1:]
        print('set: ', val, 'to: ', self.rel_path)

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

class Host(RainBase):
    __tablename__ = 'hosts'
    id = Column(Integer, primary_key=True)
    ipv4 = Column(Text, nullable=False)
    tox_pubkey = Column(Text, nullable=False)
    name = Column(String)
    pubkey = Column(Text, nullable=False)
    tcp_port = Column(Integer, nullable=False)
    udp_port = Column(Integer, nullable=False)
    
    # set by session 
    sync_id = Column(Integer, ForeignKey("syncs.id"), index=True) 
    sync = relationship("Sync", backref=backref("hosts", order_by=id )) 

    @validates('tcp_port', 'udp_port')
    def validates_port(self, key, val):
        assert val > 0
        assert val < 65535

class HostFile(RainBase):
    __tablename__ = 'host_files'
    __table_args__= (
        UniqueConstraint('host_id', 'rid'),    
    )
    id = Column(Integer, primary_key=True)

    host_id = Column(Integer, ForeignKey("hosts.id"), index=True, nullable=False) 
    host = relationship("Host", backref=backref("host_files", order_by=id ))
    
    # mapping for after file comparison
    sync_file_id = Column(Integer, ForeignKey("sync_files.id"), index=True) 
    sync_file = relationship("SyncFile", backref=backref("host_files", order_by=id))

    rid = Column(Integer, nullable=False)
    rel_path = Column(Text, nullable=False)
    file_hash = Column(Text)
    file_size = Column(Integer)
    file_parts = Column(Text)
    is_dir = Column(Boolean)
    does_exist = Column(Boolean)

class HostFileVersion(RainBase):
    ''' Store remote file version Information '''

    __tablename__ = 'host_file_versions'
    id = Column(Integer, primary_key=True)
    ver = Column(Integer, nullable=False)
    host_file_id = Column(Integer, ForeignKey("host_files.id"), index=True) 
    host_file = relationship("HostFile", backref=backref("versions", order_by=desc(ver) ))
    attrs_json = Column(Text, nullable=False)
    changes_json = Column(Text, nullable=False)

