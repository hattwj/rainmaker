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

if __name__ == "__main__":
    #########
    # logging
    logger = _lib._log.init_logger()
    
    #########
    # config
    conf= _lib._conf.RainmakerConfig()
    
    #################
    # logging to file
    _lib._log.init_file_logger(conf.log_path)
    
    #################
    # command line arguments
    parser = _lib._cli.init_parser(conf)
    args = parser.parse_args()
    _lib._cli.process_args(conf,args)

