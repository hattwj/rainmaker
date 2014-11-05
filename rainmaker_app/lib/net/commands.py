from twisted.protocols import amp

def resource_response():
    return (
        ('code', amp.Integer() ),
        ('errors', amp.ListOf( amp.String(), optional=True) )
    )

def dump_resource_errors(resource):
    result = []
    for k, reasons in resource.errors.iteritems():
        for reason in reasons:
            result.append(
                "%s:%s:%s" % (k, reason, resource.to_json())
            )
    return result

class ErrVersion(amp.AmpError):
    pass

class VersionCheckCommand(amp.Command):
    commandName = 'version_check'
    arguments = [
        ('version', amp.String())
    ]
    response = [
        ( 'response_code', amp.Integer() ),
        ( 'version', amp.String() )
    ]
    errors = {ErrVersion:'Incompatible version'}

class SetPubkeyCommand(amp.Command):
    commandName = 'set_pubkey'

    arguments = [
        ('cert', amp.String() )
    ]

    response = [
        ( 'code', amp.Integer() ),
        ( 'cert', amp.String() )
    ]

def my_file_params(optional, optional_columns=None):
    columns = ['size', 'fhash', 'inode', 'mtime', 'ctime', 'path', 'state', 'is_dir' ]
    params = []
    return amp.AmpList([
        ('path', amp.String()),
        ('fhash', amp.String() ),
        ('size', amp.Integer() ),
        ('inode', amp.Integer() ),
        ('mtime', amp.Integer() ),
        ('ctime', amp.Integer() ),
        ('state', amp.Integer() ),
        ('is_dir', amp.Boolean() )
    ], optional = optional)

class FilesResource(amp.Command):

    commandName = 'files_resource'
    arguments = [
        ('index',  amp.Boolean(optional=True)),
        ('show', amp.ListOf(amp.String(),optional=True)),
        ('create', my_file_params(optional=True)),
        ('update', my_file_params(optional=True)),
        ('delete', amp.ListOf(amp.String(),optional=True))
    ]

    response = [
        ('index', my_file_params(optional=True)),
        ('show', my_file_params(optional=True)),
        ('create', amp.AmpList([
            ('response_code', amp.Integer()),
            ('path', amp.String())
        ], optional = True)),
        ('update', amp.AmpList([
            ('response_code', amp.Integer()),
            ('path', amp.String())
        ], optional = True)),
        ('delete', amp.AmpList([
            ('response_code', amp.Integer()),
            ('path', amp.String())
        ], optional = True))
    ]


def message_params():
    return (
        ('data', amp.String() ),
        ('signature', amp.String() ),
        ('signed_at', amp.Integer() ),
        ('pubkey_str', amp.String() ),
        ('route', amp.ListOf( amp.String(), optional=True ) ),
        ('reply', amp.Boolean(optional=True) )
    )

class PostMessageCommand(amp.Command):
    commandName = 'post_message'
    arguments = [
        ('data', amp.String() ),
        ('signature', amp.String() ),
        ('signed_at', amp.Integer() ),
        ('pubkey_str', amp.String() ),
        ('route', amp.ListOf( amp.String(), optional=True ) ),
        ('reply', amp.Boolean(optional=True) )
    ]
    response = [
        ('code', amp.Integer() ),
        ('errors', amp.ListOf( amp.String(optional=True) ) )
    ]

class GetMessagesCommand(amp.Command):
    commandName = 'get_messages'
    arguments = [
        ('pubkey_str', amp.String() )
    ]

    response = [
        ('code', amp.Integer() ),
        ('post', amp.ListOf( message_params(), optional=True ) )
    ]

class PingCommand(amp.Command):
    ''' ask server to send their info '''
    commandName = 'ping'
    response = [('code', amp.Integer() )]

class ErrNotSecure(amp.AmpError):
    pass

class SecurePingCommand(amp.Command):
    ''' ask server to send their info '''
    commandName = 'secure_ping'
    response = [('code', amp.Integer() )]
    errors = {ErrNotSecure:'Connection not secure'}

class ErrAuthInit(amp.AmpError):
    pass
class ErrAuthGuid(amp.AmpError):
    pass
class ErrAuthFail(amp.AmpError):
    pass

class InitAuthCommand(amp.Command):
    commandName = 'init_auth'
    arguments = [
        ('rand', amp.String())
    ]
    response = [
        ('rand', amp.String())
    ]
class AuthCommand(amp.Command):
    commandName='auth'
    arguments = [
        ('guid', amp.String()),
        ('encrypted_password', amp.String())
    ]
    response = [
        ('encrypted_password', amp.String())
    ]
    errors = {
        ErrAuthInit: 'Init auth first',
        ErrAuthGuid: 'Unknown guid',
        ErrAuthFail: 'Invalid auth'
    }
class StoreHostCommand(amp.Command):
    commandName = 'store_host'
    arguments = [
        ('address', amp.String()),
        ('tcp_port', amp.Integer()),
        ('udp_port', amp.Integer()),
        ('pubkey_str', amp.String()),
        ('signature', amp.String()),
        ('signed_at', amp.Integer())
    ]
    response = resource_response() 

class FindHostCommand(amp.Command):
    commandName = 'find_host'
    arguments = [
        ('node_id', amp.String())
    ]
    response = resource_response() 
