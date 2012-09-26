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


root=os.path.dirname(os.path.dirname( os.path.realpath(__file__)))

sync_port = 22
menu_port = 248
base_path = '/home/rainmaker'
auth_keys_path = os.path.join( base_path, '.ssh', 'authorized_keys')
log_path = os.path.join( root, 'log', 'rainmaker.log')
daemon_log_style='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s'

