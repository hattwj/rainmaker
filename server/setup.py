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
import argparse
import app


def do_config():
    print '''
        Not implemented
        Setting up config file for rainmaker server
            in conf/config.yml
    '''
    q = [
        'port',
        'menu_port',
        'data_dir',
        'authorized_keys_file'
    ]

    port = raw_input('SSH port:') 
    port = raw_input('SSH menu port:') 

parser = argparse.ArgumentParser(version=app.version, add_help=True)
parser.add_argument('config', nargs='?', action="store")
args = parser.parse_args()

print args

if not args.config is None:
    do_config()

