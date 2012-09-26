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

"""
    Monitor server files
"""

import os
import time

# Watchdog
from watchdog.observers import Observer

import lib._log as _log
import lib._conf as _conf
from lib._fsmon import RainmakerEventHandler


def fs_event(event,eh):
    if event.event_type == 'moved':
        msg = "SRC=%s DEST=%s" % (eh.src_file_rel(event),eh.dest_file_rel(event) )  
    else:
        msg = "SRC=%s" % eh.src_file_rel(event)

    eh.log.info( "EVENT=%s %s" % (event.event_type, msg) )

base_path = _conf.base_path
xstyle=_conf.daemon_log_style

observer = Observer()
_log.init_logger(style=xstyle)
#iterate through accounts, add monitors
for p_rel in os.listdir(base_path):
    p=os.path.join(base_path, p_rel)
    watch_path = os.path.join(p,'sync') 
    log_path = os.path.join(p,'file_status.log') 
    log_f = _log.init_file_logger(fpath=log_path, name=p_rel, style=xstyle)
    eh = RainmakerEventHandler(watch_path)
    eh.log = log_f
    eh.add_callback(fs_event)

    observer.schedule(eh, watch_path, recursive=True)

observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

