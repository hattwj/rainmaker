import os, binascii

def rand_str(length):
    return binascii.b2a_base64(os.urandom(length)).decode(encoding='UTF-8')

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
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

import json
class ExportArray(list):
    
    def to_dict(self, keys=None):
        result = []
        for v in self:
            if hasattr(v, 'serialized_data'):
                result.append(v.to_json(keys))
            else:
                result.append(v)
        return result

    def to_json(self, keys=None):
        return json.dumps(self.to_dict(result, keys))
