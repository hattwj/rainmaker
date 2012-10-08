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
    rain_daemon.py
    Monitor user data files and record events to log files for each user
"""

import os
import time
import base64

# Watchdog
from watchdog.observers import Observer
#from watchdog.events import FileSystemEventHandler

import app
import app.lib._log as _log
from app.lib._fsmon import RainmakerEventHandler


def user_fs_event(self,event):
    msg = "SRC=%s" % base64.standard_b64encode(event.src_path_rel)

    if event.event_type == 'moved':
        msg += " DEST=%s" % base64.standard_b64encode(event.dest_path_rel)  
    
    self.log.info( "EVENT=%s %s" % (event.event_type, msg) )

base_path = app.config.data_path
xstyle = app.config.daemon_log_style

observer = Observer()
_log.init_logger(style=xstyle)



#iterate through accounts, add monitors
for p_rel in os.listdir(base_path):
    p=os.path.join(base_path, p_rel)
    watch_path = os.path.join(p,'sync')
    
    if not os.path.isdir(watch_path):
        os.mkdir(watch_path)

    log_path = os.path.join(p,'file_status.log') 
    log_f = _log.init_file_logger(fpath=log_path, name=p_rel, style=xstyle)
    eh = RainmakerEventHandler(watch_path,ignore_patterns=app.config.ignore_patterns)
    eh.log = log_f
    eh.add_callback(user_fs_event)
    observer.schedule(eh, watch_path, recursive=True)

observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

