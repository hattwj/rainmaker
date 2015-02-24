import os
import ujson

from rainmaker.main import Application
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
    ''' load yml file '''
    fpath = None
    if abspath:
       fpath = path 
    else:
        fpath = os.path.join(test_root, path)
    with open(fpath, 'r') as f: 
        data=f.read()
    return data
