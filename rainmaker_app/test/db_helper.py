from twisted.trial import unittest
from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from twistar.registry import Registry
from twistar.dbconfig.base import InteractionBase

from rainmaker_app.db.config import initDB, tearDownDB
from rainmaker_app.db.models import *

@inlineCallbacks
def load_fixture(test_name, data):
    if not data:
        #print "%s has no data" % test_name
        return

    #data = load('test/fixtures/unit/model/file_resolver.yml')
    if test_name not in data.keys():
        return

    for model_name, records in data[test_name].iteritems():
        if 'my_file' == model_name:
            model = MyFile
        elif 'sync_path' == model_name:
            model = SyncPath
        elif 'sync_comparison' == model_name:
            model = SyncComparison
        elif 'host' == model_name:
            model = Host
        elif 'authorization' == model_name:
            model = Authorization
        else:
            raise ValueError('unknown model: %s' % model)
        for r in records:
            record = yield model(**r).save()
            if record.errors:
                raise RuntimeError("bad %s fixture: \n%s" % (model_name, repr(record.errors)) )
