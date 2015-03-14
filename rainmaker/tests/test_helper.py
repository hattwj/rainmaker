import os
import ujson

from rainmaker.main import Application
from rainmaker.db import main as db
from rainmaker.file_system import FsActions

test_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
temp_root = os.path.abspath(
    os.path.join(os.path.dirname(
        __file__),
        '..',
        '..',
        'tmp'))
user_root = os.path.join(temp_root, 'user_root')
Application.user_root = user_root
fs = FsActions()
fs.mkdir(temp_root)
fs.mkdir(user_root)

def clean_temp_dir():
    fs.rmdir(user_root)
    fs.mkdir(user_root)

# Application file loader
def load(path, abspath=False):
    ''' load file '''
    fpath = None
    if abspath:
       fpath = path 
    else:
        fpath = os.path.join(test_root, path)
    with open(fpath, 'r') as f: 
        data=f.read()
    return data

def load_fixture(session, test_name, data):
    if not data:
        #print "%s has no data" % test_name
        return

    #data = load('test/fixtures/unit/model/file_resolver.yml')
    if test_name not in data.keys():
        return

    for model_name, records in data[test_name].items():
        if 'sync_file' == model_name:
            model = db.SyncFile
        elif 'sync' == model_name:
            model = db.Sync
        elif 'host_file' == model_name:
            model = db.HostFile
        elif 'host' == model_name:
            model = db.Host
        else:
            raise ValueError('unknown model: %s' % model_name)
        for r in records:
            record = model(**r)
            session.add(record)
    session.commit()

