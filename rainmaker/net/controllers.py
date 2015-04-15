from rainmaker.net.sessions import require_auth
from rainmaker.db.main import SyncFile, SyncPart, Host, HostFile, HostPart

def register_controllers(session, router, sync):
    auth_controller(session, router, sync.id)
    utils_controller(session, router, sync.id)
    sync_files_controller(session, router, sync.id)
    host_files_controller(session, router, sync.id)
    hosts_controller(session, router, sync.id)

def paginate(q, page, attrs=None, page_size=200):
    '''Paginate results of query'''
    if attrs is None:
        attrs = []
    q=q.limit(page_size).offset(page_size*page)
    return [f.to_dict(*attrs) for f in q]

def get_sync(db, event):
    pass

def get_host(db, event):
    pass

def tox_auth_controller(db, tox):
    '''
        Manage authentication of tox friends
    '''
    sessions = tox.sessions
    router = tox.router

    @router.responds_to('new_session')
    def _cmd_new_session(event):
        nonce = sessions.get_nonce(event.val('pk')) 
        event.reply('ok', {'nonce': nonce})

    @router.responds_to('create_session')
    def _cmd_create_session(event):
        phash = event.val('passwd_hash')
        pk = event.val('pk')
        did_auth = sessions.authenticate(pk, phash)
        if not did_auth:
            event.reply('auth fail')
            return 
        event.reply('ok')
        
def utils_controller(db, tox):
    
    @router.responds_to('ping')
    def _cmd_ping(event):
        event.reply('pong')

file_params = ['id', 'file_hash', 'file_size', 'is_dir',
    'rel_path', 'does_exist', 'version', 'ver_data']


@require_auth
def sync_files_controller(db, tox):
    '''
        db: Database session
        sync: sync path
        tr: transport
    '''
    @router.responds_to('get_sync_file')
    def _cmd_get_sync_file(event):
        ''' Handle get sync file command '''
        sync_file_id = int(event.val('id'))
        sync_file = db.query(SyncFile).filter(
            SyncFile.sync_id == sync.id,
            SyncFile.id == sync_file_id).first()
        if sync_file:
            event.reply('ok', sync_file.to_dict(*file_params))
        else:
            event.reply('not found')
    
    @router.responds_to('list_sync_files')
    def _cmd_list_sync_files(event):
        ''' Get many sync files '''
        params = event.allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        q = db.query(SyncFile).filter(
            SyncFile.sync_id == sync.id,
            SyncFile.updated_at >= since)
        sync_files = paginate(q, page)
        event.reply('ok', sync_files)
    
    @router.responds_to('list_sync_parts')
    def _cmd_list_sync_parts(event):
        params = event.require('sync_file_id').allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        id = int(params['sync_file_id'])
        q = db.query(SyncPart).filter(
            SyncPart.sync_file_id == id,
            SyncPart.updated_at >= since)
        sync_parts = paginate(q, page)
        event.reply('ok', sync_parts)

@require_auth
def hosts_controller(db, tox):
    '''
        Manage Actions For Hosts
    '''

    @router.responds_to('put_host')
    def _cmd_put_host(event):
        ''' Handle put host command '''
        p = event.get('host').require('pubkey', 'device_name').val()
        pubkey = p['pubkey']
        device_name = p['device_name']
        host = db.query(Host).filter(
                Host.sync_id == sync.id,
                Host.pubkey == pubkey).first()
        if not host:
            host = Host(sync_id=sync.id, pubkey=pubkey)
        host.device_name = device_name
        db.add(host)
        db.commit()
        event.reply('ok')
    
    @router.responds_to('list_hosts')
    def _cmd_list_hosts(event):
        params = event.allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        q = db.query(Host).filter(
            Host.sync_id == sync.id,
            Host.updated_at >= since)
        hosts = paginate(q, page)
        event.reply('put_hosts', hosts)

@require_auth
def host_files_controller(db, tox):
    '''
        db: Database session
        sync: sync path
        tr: transport
    '''
    host_file_params = ['rid', 'file_hash', 'file_size', 'is_dir',
        'rel_path', 'does_exist', 'version', 'ver_data']
    
    @router.responds_to('put_host_file')
    def _cmd_put_host_file(event):
        ''' Handle put file command '''
        p = event.get('host_file').require(*host_file_params).val()
        host_file = db.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.rid == p['rid']).first()
        if not host_file:
            host_file = HostFile()
        host_file.update_attributes(**p)
        db.add(host_file)
        db.commit()
        event.reply('ok')
    
    @router.responds_to('delete_host_file')
    def _cmd_delete_host_file(event):
        p = event.val('rid')
        host_file = db.query(HostFile).filter(HostFile.rid == rid).first()
        if host_file:
            db.delete(host_file)
            db.commit()
            event.reply('ok')
        else:
            event.reply('not found')
    
    @router.responds_to('get_host_file')
    def _cmd_get_host_file(event):
        ''' Handle get host file command '''
        p = event.val('rid')
        host_file = db.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.id == p['rid']).first()
        if host_file:
            event.reply('host_file', host_file.to_dict())
        else:
            event.reply('not found')

