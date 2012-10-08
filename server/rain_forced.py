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
import sys
from subprocess import call
import datetime
import time
import argparse

import app
from app.lib._ssh import SSHConnInfo
from app.lib._fsmon import Tail

def run(user,mode,port=None):
    if port is None:
        port = app.lib._ssh.SSHConnInfo.current_port()
    conn = app.lib._ssh.SSHConnInfo(user, port, mode)

    if conn.port == app.config.menu_port or mode == 'menu':
        run_menu(conn)
    elif conn.port == app.config.sync_port:
        run_subprocess(conn)
    else:
        RuntimeError('unkmown ssh port,')

def run_subprocess(conn):    
    if conn.mode == 'unison':
        s_cmd=['unison','-server']
        call(s_cmd)
    
def run_menu(conn):
    
    while True:
        print 'Rainmaker'
        cmd = raw_input('Thy bidding? ')
        print "ACK %s" % cmd
        if cmd == 'quit':
            print 'Bye!'
            break
        if cmd=='list':
            f = open( conn.user.log_file, 'r')
            tail = Tail(f)
            for line in tail.readlines_then_tail():
                print line
            f.close()



parser = argparse.ArgumentParser(version='0.2012.09.10',add_help=True)
parser.add_argument('--user', action="store", required=True)
parser.add_argument('--mode', action="store", required=True)
parser.add_argument('--port', action="store", type=int)
args = parser.parse_args()



try:
    run(args.user, args.mode, args.port)
except KeyboardInterrupt:
    print 'Bye!'
