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

import sys
import os
import yaml


def load_config(config_file_path,defaults):
    # Load config file
    config = {}
    if os.path.isfile(config_file_path):
        f = open(config_file_path)
        config = yaml.safe_load( f )
        f.close()
    
    # Merge the two dictionaries allowing values from the config file to override the defaults
    for k in defaults:
        if not k in config or config[k] is None:
            config[k] = defaults[k]
    
    return dict_to_object(config)

def dict_to_object(mydict):
    return type('DictToObjectClass', (object,), mydict)


root = os.path.abspath(os.path.join(os.path.dirname( __file__ ),'..','..'))
sync_port = 22
menu_port = 248
base_path = os.path.expanduser('~')
data_path = '/home/rainmaker/'
auth_keys_path = os.path.join( base_path, '.ssh', 'authorized_keys')
log_path = os.path.join( root, 'log', 'rainmaker.log')
daemon_log_style = '%(asctime)s %(name)-12s= %(levelname)-8s %(message)s'


defaults = {
    'root' : root,
    'sync_port' : sync_port,
    'menu_port' : menu_port,
    'base_path' : base_path,
    'data_path' : data_path,
    'auth_keys_path' : auth_keys_path,
    'log_path' : log_path,
    'daemon_log_style' : daemon_log_style,
    'ignore_patterns' : None
}

config_file_path = os.path.join(root,'conf','config.yml')
config = load_config(config_file_path,defaults) 
