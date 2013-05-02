import os
from rainmaker_app.lib import path, FsActions

fs = FsActions()

def install(path):
    did_install = False
    # create user's config dir
    if not os.path.isdir(path):
        did_install = True
        fs.mkdir(path)
    
    # create sub dirs too
    for p in ['tmp','plugins','log','profiles','events']:
        ipath = os.path.join(path,p)
        if not os.path.isdir( ipath ):
            fs.mkdir(ipath)

    return did_install
