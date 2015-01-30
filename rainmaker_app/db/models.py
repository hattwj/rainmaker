from rainmaker_app.model.schema_migration import SchemaMigration
from rainmaker_app.model.sync_path import SyncPath
from rainmaker_app.model.my_file import MyFile
from rainmaker_app.model.difference import Difference
from rainmaker_app.model.sync_comparison import SyncComparison
from rainmaker_app.model.authorization import Authorization
from rainmaker_app.model.host import Host
from rainmaker_app.model.host_sync_path import HostSyncPath
from rainmaker_app.model.host_file import HostFile
from rainmaker_app.model.tox_server import ToxServer

models_arr = [ 
    ToxServer, SchemaMigration, MyFile, SyncPath, Difference,
    SyncComparison, Authorization, 
    Host, HostSyncPath, HostFile
]
