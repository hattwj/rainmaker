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
import getpass

root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..') )
home_dir = os.path.expanduser('~')
rain_dir = os.path.join(home_dir,'.rainmaker')
key_file = os.path.join(home_dir,'.ssh','authorized_keys')

#
def rel(*args):
    global root
    return os.path.abspath(os.path.join(root,*args) )

# is this file executable?
def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

# search path for command
def which(program):    
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None    

# get name of current user
def current_user():
    return getpass.getuser()
