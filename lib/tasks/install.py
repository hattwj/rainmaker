import os
from lib import path

def install(path=None):
    if path == None:
        path = lib.path.rain_dir

    if not os.path.isdir(path):
        os.mkdir(path)

    for p in ['tmp','plugins','log','profiles']:
        ipath = os.path.join(path,p)
        if not os.path.isdir( ipath ):
            os.mkdir(ipath)

    #if not os.path.isdir(app.unison_dir):
    #    os.mkdir(app.unison_dir)

