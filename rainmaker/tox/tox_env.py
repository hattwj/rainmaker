from random import randint

from rainmaker.tox.tox_errors import ToxNoServersError


'''
    Singleton to hold information about tox servers
'''

__servers__ = []

def add_server(ip, port, key):
    '''
        Add a server to the list
    '''
    __servers__.append([ip, port, key])

def random_server():
    '''
        Retrieve info on random server
    '''
    if len(__servers__) == 0:
        raise ToxNoServersError()

    return __servers__[randint(0,len(__servers__)-1)]

NODES_URL = "https://wiki.tox.im/Nodes"
TIMEOUT = 30
