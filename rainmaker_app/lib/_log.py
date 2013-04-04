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

import _lib
import logging

init_done = False

# log to console
def init_logger(style='%(name)-12s %(levelname)-8s %(message)s', log_level=logging.INFO,name=''):
    global init_done
    if init_done == True:
        return
    init_done = True
    # set up logging to console
    logging.basicConfig(
        level=log_level,
        format=style
    )

# also log output to a file
def init_file_logger(fpath, name=None, style=None):
    if not style:
        style='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s'
    
    if not name:
        name = ''

    # define a Handler
    f_log = logging.FileHandler(fpath)
    f_log.setLevel(logging.DEBUG)
    # set a format which is simpler for f_log use
    formatter = logging.Formatter(style)
    # tell the handler to use this format
    f_log.setFormatter(formatter)
    # add the handler to the root name
    logging.getLogger(name).addHandler(f_log)
    
    return logging.getLogger(name)

