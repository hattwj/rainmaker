from . common import *

from rainmaker_app.lib.lib_hash import RollingHash

class HostSyncPath(Base):
    ''' Model status of file system between scans '''

    HASMANY = ['host_files']
    BELONGSTO = ['host']


