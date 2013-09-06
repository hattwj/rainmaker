import unittest
import os

from twisted.internet import defer,reactor
from rainmaker_app.test import test_helper

from rainmaker_app.db.config import initDB
from rainmaker_app.db.model import *


@defer.inlineCallbacks
def main(db, sync_path):
    print 'Starting....'
    yield initDB(db)    
    sp = yield SyncPath.findOrCreate(root='/home/ubuntu/sync')
    gg = yield sp.scan()
    reactor.stop()

location = os.path.join(test_helper.user_dir, 'test.sqlite')
sync_path = os.path.join(test_helper.temp_dir, 'sync_path1')

reactor.callLater(0, main, location, sync_path)
reactor.run()  
