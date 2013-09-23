from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor

from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

from rainmaker_app.db.config import initDB, tearDownDB
from rainmaker_app.db.model import *


@inlineCallbacks
def load_fixture(test_name, data):
    #data = load('test/fixtures/unit/model/file_resolver.yml')
    if test_name not in data.keys():
        return

    for table, rows in data[test_name].iteritems():
        for r in rows:
            if 'my_file' == table:
                yield MyFile(**r).save()
            elif 'sync_path' == table:
                yield SyncPath(**r).save()
            elif 'sync_comparison' == table:
                yield SyncComparison(**r).save()

