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
import _conf

User.base_path = _conf.data_path

class SSHConnInfo(object):
    "hold information regarding an ssh connection"
     
    def __init__(self,name, port=None, mode=None):
        self.port = port
        self.mode = mode
        self.user = User.find_by_name(name)

    @staticmethod
    def current_port():
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

        return port

class AuthorizedKeys(object):
    def __init__(self,path):
        "init"
        self.path = path
        self.r = re.compile('^(ssh-dss|ssh-rsa) ([A-Za-z0-9\/\+]+={0,3}) ?([A-Za-z0-9\/\+@]+)?')
   

    def parse_key(self,val):
        note = None
        
        m=self.r.findall(val)
        
        if not m:
            raise RuntimeError('malformed or unsupported key')
    
        if not m[0][0]:
            raise RuntimeError('missing key type')
        
        if not m[0][1]:
            raise RuntimeError('missing key')
        
        if m[0][2]:
            note=m[0][2]
        
        keytype=m[0][0]
        pubkey=m[0][1]
    
        if len(pubkey)%4 < 0:
            raise RuntimeError('key is invalid base 64')
        
        if 30 > len(pubkey):
            raise RuntimeError('key too short')
        
        if 1000 < len(pubkey):
            raise RuntimeError('key too long') 
    
        result = { 
            'key_type': keytype,
            'pub_key' : pubkey,
            'note' : note,
            'opts' : [],
            'command' : None
            }
        return result
    
    def backup_keys(self):
        pass
        print 'not implemented'

    def key_unique(self,key):
        result = True

        f = open(self.path,'r')
        for line in f.readlines():
            if key['pub_key'] in line:
                result = False
        f.close()
        return result

    def format_line(self,key):
        
        line = '%s %s %s' % (key['key_type'], key['pub_key'],key['note'])
        
        if key['opts']:
            line = '%s %s' % (' '.join(key['opts']), line )

        if key['command']:
            line = 'command="%s" %s' % (key['command'], line)
        
        return line

    def add_key(self, line, user, command):
        key = self.parse_key(line)
        key['opts'].append('no-x11-forwarding')
        key['command'] = command

        if not self.key_unique(key):
            raise RuntimeError('Key exists already')
        auth_line = self.format_line(key)
        print auth_line
        
        #add to authorized keys
        f=open(self.path,'a')
        f.write("%s\n" % auth_line)
        f.close()
        print "Written to: %s" % self.path

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
