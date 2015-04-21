from sqlalchemy.orm import subqueryload, joinedload
from rainmaker.net.sessions import controller_requires_auth
from rainmaker.db.main import Sync, SyncFile, SyncPart, Host, HostFile, HostPart

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

def tox_auth_controller(db, tox):
    '''
        Manage authentication of tox friends
    '''
    sessions = tox.sessions
    router = tox.router
    sync = tox.sync

    @router.responds_to('new_session')
    def _cmd_new_session(event):
        nonce = sessions.get_nonce(event.val('pk')) 
        event.reply('ok', {'nonce': nonce})

    @router.responds_to('create_session')
    def _cmd_create_session(event):
        params = event.require('pk', 'passwd_hash').allow('device_name').val()
        phash = params['passwd_hash']
        pk = params['pk']
        dname = params.get('device_name', 'unknown')
        did_auth = sessions.authenticate(pk, phash)
        if not did_auth:
            event.reply('auth fail')
            return
        host = db.query(Host).filter(
            Host.pubkey==pk, 
            Host.sync_id==sync.id).first() 
        if not host:
            host = Host(pubkey=pk, sync_id=sync.id, device_name=dname)
            db.add(host)
            db.commit()
        sessions.put(pk, 'host', host)
        event.reply('ok', host.to_dict())
        
def utils_controller(db, transport):
    router = transport.router

    @router.responds_to('ping')
    def _cmd_ping(event):
        event.reply('pong')

file_params = ['id', 'file_hash', 'file_size', 'is_dir',
    'rel_path', 'does_exist', 'version', 'ver_data']

@controller_requires_auth
def sync_files_controller(db, transport):
    '''
        limit access:
        - transport has sync
        - session can store
    '''
    router = transport.router
    sessions = transport.sessions
    sync = transport.sync

    @router.responds_to('get_sync_file')
    def _cmd_get_sync_file(event):
        ''' Handle get sync file command '''
        sync_file_id = int(event.val('sync_file_id'))
        sync_file = db.query(SyncFile).options(
                subqueryload('sync_parts')
                ).filter(
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
        event.reply('ok', {'sync_files':sync_files})
 
@controller_requires_auth
def sync_parts_controller(db, transport):
    '''
    '''
    router = transport.router
    sessions = transport.sessions
    sync = transport.sync

    @router.responds_to('list_sync_parts')
    def _cmd_list_sync_parts(event):
        params = event.require('sync_file_id').allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        id = int(params['sync_file_id'])
        q = db.query(SyncPart).filter(
            SyncPart.sync_file_id == id,
            SyncPart.updated_at >= since).filter(
            SyncFile.id == id).filter(Sync.id == sync.id)
        sync_parts = paginate(q, page)
        event.reply('ok', {'sync_parts':sync_parts})

@controller_requires_auth
def hosts_controller(db, transport):
    '''
        Manage Actions For Hosts
    '''
    router = transport.router
    sessions = transport.sessions
    sync = transport.sync

    @router.responds_to('update_host')
    def _cmd_update_host(event):
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
        event.reply('ok', {'hosts': hosts})

@controller_requires_auth
def host_files_controller(db, transport):
    '''
        db: Database session
        sync: sync path
        tr: transport
    '''
    router = transport.router
    sessions = transport.sessions
    sync = transport.sync

    host_file_params = ['rid', 'file_hash', 'file_size', 'is_dir',
        'rel_path', 'does_exist', 'version', 'ver_data']
    
    @router.responds_to('list_host_files')
    def _cmd_list_host_files(event):
        hfi = event.get('host_file_id')
        q = db.query(HostPart).filter(
            HostPart.sync_file_id == id,
            HostPart.updated_at >= since).filter(
            Sync.id == sync.id)
        sync_parts = paginate(q, page)


    @router.responds_to('put_host_file')
    def _cmd_put_host_file(event):
        ''' Handle put file command '''
        pk = event.val('pk')
        p = event.get('host_file').require(*host_file_params).val()
        host = sessions.get(pk, 'host')
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
            event.reply('ok', host_file.to_dict())
        else:
            event.reply('not found')

