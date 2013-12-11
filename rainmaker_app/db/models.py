from rainmaker_app.model.schema_migration import SchemaMigration
from rainmaker_app.model.sync_path import SyncPath
from rainmaker_app.model.my_file import MyFile
from rainmaker_app.model.difference import Difference
from rainmaker_app.model.file_version import FileVersion
from rainmaker_app.model.sync_comparison import SyncComparison
from rainmaker_app.model.authorization import Authorization
from rainmaker_app.model.message import Message
from rainmaker_app.model.pubkey import Pubkey
from rainmaker_app.model.host import Host
from rainmaker_app.model.broadcast import Broadcast

models_arr = [ 
    SchemaMigration, MyFile, SyncPath, Difference,
    FileVersion, SyncComparison, Authorization, 
    Message, Pubkey, Host, Broadcast
]
