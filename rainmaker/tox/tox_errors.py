'''
    Errors
'''
class ToxBaseError(Exception):
    def __init__(self, msg=None):
        if msg is not None:
            self.message = msg
        super(Exception, self).__init__(self.message)

class ToxConnectionError(ToxBaseError):
    '''
        Unknown error while connecting to dht
    '''
    message = 'Unknown error while connecting to dht'

class ToxNoPeersError(ToxConnectionError):
    '''
        NoPeers
    '''
    message = 'No peers to send to'

class ToxClientError(ToxBaseError):
    '''
        Generic client error
    '''
    message = 'Generic client error'

class ToxAuthorizationError(ToxClientError):
    '''
        Unauthorized command from client
    '''
    message = 'Unauthorized command from client'

class ToxCommandError(ToxClientError):
    '''
        Unknown command from client
    '''
    message = 'Unrecognized command from client'

class ToxNoServersError(ToxBaseError):
    '''
        No tox server addresses loaded
    '''
    message = 'There are no tox servers addresses loaded'
