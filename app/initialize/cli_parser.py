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

import argparse

from lib import logger
class CliParser(object):
    # initialize command line parser
    def __init__(self):
        actions = ['create','delete','list','update','start','stop','status','auto']
        parser = argparse.ArgumentParser(version='0.0.2',add_help=True)
        parser.add_argument('action',choices=actions)
        parser.add_argument('--log', action="store", dest='log_level', choices=logger.levels, default='warn')
        self.parser=parser
    
    def parse(self,args):
        return self.parser.parse_args(args)
