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
#import sys
import os
from queue import Queue, Empty  # python 3.x

# Watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from rainmaker.db.main import SyncFile
from rainmaker.sync_manager.scan_manager import refresh_sync, scan_dir, scan_file

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

observer = None

def SyncWatch(session, sync):
    
    queue = Queue()

    class EventHandler(FileSystemEventHandler):
        
        def dispatch(self, event):
            ''' store events for later '''
            queue.put(event)
            
        def commit(self):
            ''' run events '''
            did_get = False
            while True:
                try:
                    # raise events
                    event = queue.get_nowait()
                    super(EventHandler, self).dispatch(event)
                    did_get = True
                except Empty as e:
                    break
            if did_get:
                # refresh db if modifications occurred
                session.commit()
                refresh_sync(session, sync)

        """ File System Events """
        def on_moved(self, event):
            log.info('moved', event)
            sync_path = session.query(SyncFile).filter(
                SyncFile.is_dir     == event.is_directory,
                SyncFile.rel_path   == sync.rel_path(event.src_path),
                SyncFile.sync_id    == sync.id,
                SyncFile.does_exist == True).first()
            sync_path.rel_path = sync.rel_path(event.dest_path)
            session.add(sync_path)
        
        def on_created(self, event):
            log.info('created')
            sync_file = SyncFile(
                is_dir     = event.is_directory,
                rel_path   = sync.rel_path(event.src_path),
                sync_id    = sync.id,
                does_exist = True)
            session.add(sync_file)
            
        def on_deleted(self, event):
            # find, mark deleted
            log.info('deleted', event)
            sync_path = session.query(SyncFile).filter(
                SyncFile.is_dir     == event.is_directory,
                SyncFile.rel_path   == sync.rel_path(event.src_path),
                SyncFile.sync_id    == sync.id,
                SyncFile.does_exist == True).update({'does_exist': False})
            if event.is_directory:
                flike = '%s%s%s' % (sync.rel_path(event.src_path), os.pathsep, '%')
                sync_path = session.query(SyncFile).filter(
                    SyncFile.is_dir     == event.is_directory,
                    SyncFile.rel_path.like(flike),
                    SyncFile.sync_id    == sync.id,
                    SyncFile.does_exist == True).\
                        update({'does_exist': False}, False)
         
        def on_modified(self, event):
            # find, check stime_start and possibly scan
            if not event.is_directory:
                log.info('modified', event)
                sync_path = session.query(SyncFile).filter(
                    SyncFile.is_dir     == event.is_directory,
                    SyncFile.rel_path   == sync.rel_path(event.src_path),
                    SyncFile.sync_id    == sync.id,
                    SyncFile.does_exist == True).update({'stime_start':0})
    
    eh = EventHandler()
    observer.schedule(eh, sync.path, recursive = True)
    return eh

def init():
    global observer
    observer = Observer()
    observer.start()

def stop():
    global observer
    observer.stop()
    observer.join()
