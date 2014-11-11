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
        ( 'cert', amp.String() )
    ]


def my_file_params(optional=None):
    return [
        ('path', amp.String() ),
        ('fhash', amp.String() ),
        ('size', amp.Integer() ),
        ('inode', amp.Integer() ),
        ('mtime', amp.Integer() ),
        ('ctime', amp.Integer() ),
        ('state', amp.Integer() ),
        ('is_dir', amp.Boolean() )
    ]

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
class ErrAuthRand(amp.AmpError):
    pass
class ErrAuthSyncPath(amp.AmpError):
    pass
class ErrAuthFail(amp.AmpError):
    pass

class AuthCommand(amp.Command):
    commandName='auth'
    arguments = [
        ('rand', amp.String()),
        ('guid', amp.Unicode()),
        ('enc_pass', amp.String())
    ]
    response = [
        ('rand', amp.String()),
        ('enc_pass', amp.String())
    ]
    errors = {
        ErrAuthInit: 'Can only be run once',
        ErrAuthRand: 'Random value has error',
        ErrAuthSyncPath: 'SyncPath not found',
        ErrAuthFail: 'Authentication Failed'
    }


def sync_path_params():
    return [
        ('state_hash',              amp.String()),
        ('state_hash_updated_at',   amp.Integer()),
        ('updating',                amp.Boolean()),
        ('guid',                    amp.Unicode())
    ]

class GetSyncPathCommand(amp.Command):
    commandName='sync_path'
    arguments = sync_path_params()
    response = sync_path_params()

def file_params():
    return (
        ('path', amp.String() ),
        ('fhash', amp.String() ),
        ('size', amp.Integer() ),
        ('inode', amp.Integer() ),
        ('mtime', amp.Integer() ),
        ('ctime', amp.Integer() ),
        ('state', amp.Integer() ),
        ('is_dir', amp.Boolean() )
    )

class PutFilesCommand(amp.Command):
    commandName='my_files'
    arguments  = [
        ('files', amp.ListOf(my_file_params()))
    ]

