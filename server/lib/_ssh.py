#!/usr/bin/python
"""
This file is part of Rainmaker.

    Rainmaker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Rainmaker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Rainmaker.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import sys

from _user import User


# modified in __init__.py
authorized_keys_path = '/home/rainmaker/.ssh/authorized_keys'

class SSHConnInfo(object):
    "hold information regarding an ssh connection"
     
    def __init__(self,name, port=None, mode=None):
        self.port = port
        self.mode = mode
        self.user = User.find_by_name(name)

    @staticmethod
    def current():
        "return info about current connection"
        conn_info = os.environ['SSH_CONNECTION']
        port_re = re.compile('([0-9]+)$')
        m = port_re.findall(conn_info)
        
        port = None
        if not m:
            RuntimeError('unable to parse connection info')
        for g in m:
            port = int(g)
            break

        user_id = sys.argv[1]
        mode = sys.argv[2]

        conn = SSHConnInfo(name=user_id,port=port, mode=mode)
        return conn


def parse_key(val,user):
    p3=re.compile('^(ssh-dss|ssh-rsa) ([A-Za-z0-9\/\+]+={0,3}) ?([A-Za-z0-9\/\+@]+)?')
    m=p3.findall(val)
    
    if not m:
        raise RuntimeError('malformed or unsupported key')

    if not m[0][0]:
        raise RuntimeError('missing key type')
    
    if not m[0][1]:
        raise RuntimeError('missing key')
    
    if not m[0][2]:
        note = ''
        print('missing note')
    else:
        note=m[0][2]
    
    keytype=m[0][0]
    pubkey=m[0][1]

    if len(pubkey)%4 < 0:
        raise RuntimeError('key is invalid base 64')
    
    if 30 > len(pubkey):
        raise RuntimeError('key too short')
    
    if 1000 < len(pubkey):
        raise RuntimeError('key too long')
    note='user=%s' % user
    result = 'no-X11-forwarding command="unison -server" %s %s %s' % (keytype,pubkey,note)
    return result

def backup_keys(self):
    pass
    #os.path.copy(p,)

def add_key(key,user):
    global key_file
    line = parse_key(key,user)
    print "Key: %s" % line

    #add to authorized keys
    f=open(key_file,'a')
    f.write("%s\n" % line)
    f.close()
    print "Written to: %s" % key_file

import paramiko
import time
def ssh():
    privatekeyfile = os.path.expanduser('~/.ssh/rain')
    mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
    
    ssh = paramiko.SSHClient()
    kh = os.path.expanduser('~/.ssh/known_hosts')
    ssh.load_system_host_keys( kh)
    ssh.load_host_keys(kh)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('localhost', username = 'ubuntu', pkey = mykey, port=248)
    
    print 'open session...'
    
    c=ssh.invoke_shell()
    #print c.recv(5)
    while True:
        if c.exit_status_ready():
            print c.recv_exit_status()
            print 'Hung up'
            break 
        else:
            print 'nox'
        if c.recv_ready():
            print 'RECIEVED:'
            print c.recv(1024)
        r=raw_input('check')
        if r=='q':
            break
        if c.send_ready() and r !='':
            print "SENT: %s" % r
            c.send("%s\n" % r)
    ssh.close()
