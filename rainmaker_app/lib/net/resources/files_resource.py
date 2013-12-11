from twisted.internet import defer
from rainmaker_app.db.models import MyFile

@defer.inlineCallbacks
def delete(server, paths):
    my_files = yield MyFile.find_many(paths, col='path', where=['sync_path_id = ?', server.sync_path.id])
    result = []
    for f in my_files:
        g = yield f.delete()
        result.append( {'response_code':100,'path': str(f.path)} )
    defer.returnValue({'delete':result})

@defer.inlineCallbacks
def show(server, paths):
    my_files = yield MyFile.find_many(paths, col='path', where=['sync_path_id = ?', server.sync_path.id])
    result = []
    for f in my_files:
        result.append( f.to_dict() )
    defer.returnValue({'show' : result})

@defer.inlineCallbacks
def index(server, paths):
    my_files = yield MyFile.find(where=['sync_path_id = ?', server.sync_path.id])
    result = []
    for f in my_files:
        result.append( f.to_dict() )
    result = {
        'path':  'a', 
        'fhash': 'b',
        'size':  1,
        'inode': 3,
        'mtime': 3,
        'ctime': 4, 
        'state': 2,
        'is_dir': False
    }
    defer.returnValue({'index' : [result] })
