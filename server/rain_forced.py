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
import logging
import os
import re
import sys

from subprocess import call
import datetime

import lib._ssh
import sys
import time
import logging

from lib._ssh import SSHConnInfo
from lib._fsmon import Tail
import lib._conf as conf

def run():
    conn = SSHConnInfo.current()
    if 'menu' in sys.argv:
        conn.port = conf.menu_port

    if conn.port == conf.menu_port:
        run_menu(conn)
    elif conn.port == conf.sync_port:
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

if __name__ == "__main__":

    try:
        run()
    except KeyboardInterrupt:
        print 'Bye!'
