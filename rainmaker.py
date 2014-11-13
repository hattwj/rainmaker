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
from twisted.internet import reactor, threads
from rainmaker_app import boot, lib

def main():
    ''' Run the application ''' 
    # rainmaker_app must be in py_path
    sys.path.insert(1, lib.path.root)
    boot.init_pre()
    d = boot.init_app()
    d.addCallback(start)

def start(pp):
    boot.init_network()
    if not boot.app.start_console:
        boot.start_network()
    else:
        from rainmaker_app import console
        threads.deferToThread(console.run)

if __name__ == "__main__":
    main()
    reactor.run()

