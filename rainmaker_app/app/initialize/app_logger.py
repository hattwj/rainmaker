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
from rainmaker_app.lib import logger

class AppLogger(object):
    def __init__(self,my_app):
        #  
        self.app = my_app
        # set up logging to console
        logger.do_init(level=self.app.log_level,style=self.app.log_style)
        self.app.log=logger.create()
        
        # setup logging to file
        logger.send_log_to_file(self.app.log_path,self.app.log)
        self.app.log.debug('Starting logger...')
