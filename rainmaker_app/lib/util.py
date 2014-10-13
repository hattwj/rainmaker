from collections import defaultdict
from twisted.internet import defer
class DeferredDict(dict):
    def __init__(self, *args, **kwargs):
        self._deferreds = defaultdict(set)
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, item):
        try:
            return defer.succeed(dict.__getitem__(self, item))
        except KeyError:
            d = defer.Deferred()
            self._deferreds[item].add(d)
            return d

    def __setitem__(self, item, value):
        # check/ delete if already set
        if item in self._deferreds:
            for d in self._deferreds[item]:
                d.callback(value)
            del self._deferreds[item]
        # set
        dict.__setitem__(self, item, value)

from time import time

def time_now():
    '''
        Return current time stamp in Unix milliseconds
    '''
    return int( round( time() * 1000 ) )


def assign_attrs(obj, **kwargs):
    ''' Assign Attributes to self '''
    for k, v in kwargs.iteritems():
        if hasattr(obj, k):
            setattr(obj, k, v)
        else:
            raise AttributeError('Unknown attribute: %s' % k)
import re
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

class Object:
    ''' Anonymous Object class'''
    pass

import json
class ExportArray(list):
    def to_json(self):
        result = []
        for v in self:
            if hasattr(v, 'serialized_data'):
                result.append(v.serialized_data)
            else:
                result.append(v)
        return json.dumps(result)
