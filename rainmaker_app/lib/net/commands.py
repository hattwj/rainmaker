from twisted.protocols import amp

def resource_response():
    return {
        'response' : {
            'code' : 200,
            'errors' : []
        }
    }

class VersionCheckCommand(amp.Command):
    commandName = 'version_check'
    arguments = [
        ('version', amp.String())
    ]
    response = [
        ( 'response_code', amp.Integer() ),
        ( 'version', amp.String() )
    ]

class SetPubkeyCommand(amp.Command):
    commandName = 'set_pubkey'

    arguments = [
        ('guid', amp.String() )
    ]

    response = [
        ( 'response_code', amp.Integer() ),
        ( 'message', amp.String() )
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


def message_params(optional):
    return amp.AmpList([
        ('message': amp.String() ),
        ('signature': amp.String() ),
        ('pubkey_str': amp.String())
    ], optional = optional)


class MessageResource(amp.Command):
    commandName = 'public_host_resource'
    arguments = [
        ('post', message_params(optional=True) ),
        ('index', amp.AmpList([
            ('pubkey_str': amp.String() )
        ], optional=True) )
    ]

    response = [
        ('post', message_params(optional=True)),
        ('index', message_params(optional=True))
    ]
