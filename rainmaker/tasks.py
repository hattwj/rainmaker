# Python imports
from __future__ import print_function
import os

from rainmaker.db.main import init_db
from rainmaker.tox.main import init_tox
from rainmaker.sync_manager.main import init_sync

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)


from rainmaker.main import Application


def autorun(self):
    log.info("Starting rainmaker version: %s" % self.version)
    log.info('Checking installation...')
    # create user's config dir
    if not os.path.isdir(self.user_dir):
        did_install = True
        self.fs_log.mkdir(self.user_dir) 
        self.fs_log.touch(self.db_path)

    log.info('Initializing db...') 
    self.db = rainmaker.db.main.init_db(self.db_path)

    if self.start_tox:
        log.info('Configuring Tox...')
        rainmaker.tox.main.init_tox(self.db)
    else:
        log.info('Skipping Tox...')

    if self.start_sync:
        log.info('Initializing Sync Managers...')
        rainmaker.sync_manager.main.init_sync(self.db)
    else:
        log.info('Skipping Sync auto start')

Application.autorun = autorun
