import os
import shutil
import yaml
import sys

from rainmaker_app import boot, app

#boot.pre_init()

root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..') )

temp_dir = os.path.join(root, 'tmp')
fixtures_dir = os.path.join(root, 'test', 'fixtures')
user_dir = os.path.join(temp_dir, '.rainmaker')
events_dir = os.path.join(temp_dir, 'events')
backups_dir = os.path.join(temp_dir, 'backups')
data_dir = os.path.join(temp_dir, 'sync1')
db_path = os.path.join(user_dir, 'test.sqlite')

app.paths = [os.path.join(root, 'conf')]
app.root = root
app.user_dir = user_dir
app.temp_dir = temp_dir
app.events_dir = events_dir
app.backups_dir = backups_dir
app.data_dir = data_dir
app.db_path = db_path
app.config_path = app.paths[0]

from rainmaker_app.tasks.install import run as install
from rainmaker_app.lib import logger, util
from rainmaker_app.lib.fs_actions import FsActions
import rainmaker_app

fs = FsActions()
logger.config['level']='warn'
logger.verbosity = 0
logger.create('Tests',level='warn')

from random import random
def write_many(path, count=10):
    '''
        create many random files
        return their paths
    '''
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
        install()
        fs.mkdir(backups_dir)
        fs.mkdir(events_dir)
        fs.mkdir(data_dir)

    for tdir in tdirs:
        tdir = os.path.join(temp_dir,tdir)
        fs.rmdir(tdir)
        if create:
            fs.mkdir(tdir)

def load(path,abspath=False,from_dir=None, raw=False):
    ''' Load yml path rel to root '''
    from_dir = from_dir if from_dir else root
    if not abspath: 
        path = ('%s/%s' % (from_dir,path)).split('/') 
        path = os.path.sep.join(path)
    with open( path,'r') as f: 
        if raw:
            return f.read()
        data=yaml.safe_load(f.read())
    return data

clock_offset = 0
def time_elapsed(interval=0,reset=False):
    global clock_offset
    if reset:
        clock_offset = 0
    else:
        clock_offset += interval

from time import time
def time_now():
    '''
        Return current time stamp in Unix milliseconds
    '''
    #print 'time called with offset'
    global clock_offset
    return int( round( time() * 1000 ) ) + clock_offset

util.time_now = time_now
