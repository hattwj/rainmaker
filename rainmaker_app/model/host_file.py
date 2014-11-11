from . common import *
from rainmaker_app.lib.lib_hash import md5Checksum as checksum

class HostFile(Base):

    BELONGSTO = ['host_sync_path']

