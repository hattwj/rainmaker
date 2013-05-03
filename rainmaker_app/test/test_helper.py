import os
import shutil
import yaml
from rainmaker_app.tasks import install
from rainmaker_app.lib import logger
from rainmaker_app.lib import FsActions

logger.config['level']='debug'
logger.verbosity = 4

root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..') )
temp_dir = os.path.join(root,'tmp')
user_dir = os.path.join(temp_dir,'.rainmaker')
events_dir = os.path.join(temp_dir,'events')
backups_dir = os.path.join(temp_dir,'backups')

fs = FsActions()

def clean(tdirs=[],create=True):
    fs.rmdir(user_dir)
    fs.rmdir(events_dir)
    fs.rmdir(backups_dir)
    if create:
        install(user_dir)
        fs.mkdir(backups_dir)
        fs.mkdir(events_dir)
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

