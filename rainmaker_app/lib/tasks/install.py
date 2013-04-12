import os
from rainmaker_app.lib import path

def install(path):
    
    # create user's config dir
    if not os.path.isdir(path):
        os.mkdir(path)
    
    # create sub dirs too
    for p in ['tmp','plugins','log','profiles','events']:
        ipath = os.path.join(path,p)
        if not os.path.isdir( ipath ):
            os.mkdir(ipath)
