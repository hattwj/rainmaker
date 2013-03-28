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
import paramiko
import time

class Client(object):
    def __init__(self,**kwargs):
        self.running = False
        self.opts = {
            'port' : 22,
            'known_hosts' :  os.path.expanduser('~/.ssh/known_hosts'),
            'user' : None,
            'host' : None,
            'private_key' : os.path.expanduser('~/.ssh/id_rsa')
        }

        for k in kwargs:
            self.opts[k]=kwargs[k]

        self.ssh = paramiko.SSHClient()

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        
        self.ssh.load_system_host_keys(self.opts['known_hosts'])
        self.ssh.load_host_keys(self.opts['known_hosts'])
        self.mykey = paramiko.RSAKey.from_private_key_file(self.opts['private_key'])
        self.ssh.connect(self.opts['host'], username = self.opts['user'], pkey = self.mykey, port=self.opts['port'])
        
        self.running = True
        print 'open session...'
        self.c=self.ssh.invoke_shell()
    

    def list(self):
        msg='list'
        lines =''
        self.state = 'connecting'
        while self.running:
            print self.state
            time.sleep(1)
            if self.c.exit_status_ready():
                print self.c.recv_exit_status()
                self.running = False
                self.state = 'hung_up'
                self.close()
                break 
        
            if self.c.recv_ready() and self.state=='connecting':
                print 'RECIEVED:'
                print self.c.recv(1024)
                self.state = 'sending'
                next
            
            if self.c.send_ready() and self.state=='sending':
                print "SENT: %s" % msg
                self.c.send("%s\n" % msg)
                msg = ''
                self.state = 'tailing'
                return
    
    def new_lines(self):
        lines = ''
        if self.running==False:
            raise RuntimeError('ssh client not running')
            
        time.sleep(1)
        if self.c.exit_status_ready():
            print self.c.recv_exit_status()
            self.running = False
            self.state = 'hung_up'
            self.close()
             
        if self.c.recv_ready() and self.state=='tailing':
            while self.c.recv_ready() and len(lines)<4096:
                lines += self.c.recv(1024)
        
        if "\n" in lines:
            while  "\n" in lines:
                print 7
                line,lines=lines.split("\n",1)
                if line:
                    yield line

    def close(self):
        self.ssh.close()
        self.running=False
