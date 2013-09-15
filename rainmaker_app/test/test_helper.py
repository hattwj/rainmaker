import os
import shutil
import yaml
import sys

#module_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..') )
#sys.path.append(module_path)

from rainmaker_app.tasks import install
from rainmaker_app.lib import logger
from rainmaker_app.lib import FsActions

logger.config['level']='warn'
logger.verbosity = 0
logger.create('Tests',level='warn')

root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..') )

temp_dir = os.path.join(root, 'tmp')
fixtures_dir = os.path.join(root, 'test', 'fixtures')
user_dir = os.path.join(temp_dir, '.rainmaker')
events_dir = os.path.join(temp_dir, 'events')
backups_dir = os.path.join(temp_dir, 'backups')
data_dir = os.path.join(temp_dir, 'sync1')
db_path = os.path.join(user_dir, 'test.sqlite')

fs = FsActions()

from random import random
def write_many(path,count=10):
    result = []
    for n in range(0, count):
        cur_path = os.path.join(path, str(random()) )
        fs.write(cur_path, str(random()) )
        result.append(cur_path)
    return result

def clean_temp_dir(tdirs=[],create=True):
    fs.rmdir(user_dir)
    fs.rmdir(events_dir)
    fs.rmdir(backups_dir)
    fs.rmdir(data_dir)
    if create:
        install(user_dir)
        fs.mkdir(backups_dir)
        fs.mkdir(events_dir)
        fs.mkdir(data_dir)

    for tdir in tdirs:
        tdir = os.path.join(temp_dir,tdir)
        fs.rmdir(tdir)
        if create:
            fs.mkdir(tdir)

def load(path,abspath=False,from_dir=None):
    ''' Load yml path rel to root '''
    from_dir = from_dir if from_dir else root
    if not abspath: 
        path = ('%s/%s' % (from_dir,path)).split('/') 
        path = os.path.sep.join(path)
    with open( path,'r') as f: 
        data=yaml.safe_load(f.read())
    return data

