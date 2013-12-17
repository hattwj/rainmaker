import os
from twisted.internet import reactor, task

from rainmaker_app.lib.net import cert
from rainmaker_app.test.test_helper import fs, temp_dir


base_path = os.path.join(temp_dir, 'keys')
fs.mkdir(base_path)
k_path = os.path.join(base_path, 'key')
c_path = os.path.join(base_path, 'cert')

if not (os.path.exists(c_path) and os.path.exists(k_path)):
    key, crt = cert.create_self_signed_cert() 
    f = open(c_path,'wt')
    f.write(crt)
    f.close()

    f = open(k_path,'wt')
    f.write(key)
    f.close()

