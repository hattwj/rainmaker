import os
import app.lib._ssh as ssh
import app

path = os.path.join(app.root,'tmp','authorized_keys')
pub_key_path = '/home/ubuntu/.ssh/rain.pub'
user = 'ubuntu'
mode = 'unison'
forced_cmd = os.path.join(app.root,'rain_forced.py --user %s --mode %s' % (user, mode) )

f=open(pub_key_path,'r')
pub_key = f.readline()
f.close()

g = ssh.AuthorizedKeys(path)
g.add_key(pub_key,'ubuntu',forced_cmd)

