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
import lib.logger


class AppLogger(object):
    def __init__(self,my_app):
        self.app = my_app
        self.style='%(name)-12s %(levelname)-8s %(message)s'
        self.level='info'
        self.levels = {'debug' : logging.DEBUG,
        'warn' : logging.WARN,
        'error' : logging.ERROR,
        'info' : logging.INFO}
        self.app.callbacks.register('before_init',self.before_app_init) 

    def before_app_init(self,**kwargs):
        # set up logging to console
        lib.logger.do_init(level=self.levels[self.level],style=self.style)
        self.app.log=lib.logger.create()
        lib.logger.send_log_to_file(self.app.log_path,self.app.log)
        self.app.log.info('Init starting...')
