from twisted.internet import defer
from rainmaker_app.db.models import MyFile

@defer.inlineCallbacks
def delete(sync_path, paths):
    my_files = yield MyFile.find_many(paths, col='path', where=['sync_path_id = ?', sync_path.id])
    result = []
    for f in my_files:
        g = yield f.delete()
        result.append( {'response_code':100,'path': str(f.path)} )
    defer.returnValue({'delete':result})

@defer.inlineCallbacks
def show(sync_path, paths):
    my_files = yield MyFile.find_many(paths, col='path', where=['sync_path_id = ?', sync_path.id])
    result = []
    for f in my_files:
        result.append( f.to_dict() )
    defer.returnValue({'show' : result})

@defer.inlineCallbacks
def index(sync_path, paths):
    my_files = yield MyFile.find(where=['sync_path_id = ?', sync_path.id])
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
