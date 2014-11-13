import os
from rainmaker_app.lib import path
from rainmaker_app.lib.fs_actions import FsActions
from rainmaker_app import app

fs = FsActions()

def run():
    did_install = False
    # create user's config dir
    if not os.path.isdir(app.user_dir):
        did_install = True
        fs.mkdir(app.user_dir)
     
    # create sub dirs too
    for p in ['tmp','plugins','log']:
        ipath = os.path.join(app.user_dir, p)
        if not os.path.isdir( ipath ):
            fs.mkdir(ipath)
    print app.user_dir
    print app.config_path
    #if not os.path.exists(app.database_path):
    #    app.fs.touch(app.database_path)
    if not os.path.exists(app.config_path):
        config_path = os.path.join(app.root,'conf', 'config.yml')
        app.fs.copy(config_path, app.config_path)
        line = "machine_name: %s\n" % gen_machine_name()
        app.fs.append(app.config_path, line)

    return did_install


def gen_machine_name():
    import socket
    return socket.gethostname()


