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
        ('machine_name',              amp.String()),
        ('rolling_hash',              amp.String()),
        ('state_hash',              amp.String())
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
        ('files', amp.ListOf(file_params()))
    ]

