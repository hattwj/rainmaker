from sqlalchemy.orm import subqueryload, joinedload
from rainmaker.net.sessions import controller_requires_auth
from rainmaker.db.main import Sync, SyncFile, Host, HostFile
from rainmaker.db import views

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)


def register_controller_routes(DbConn, transport):
    tox_auth_controller(DbConn, transport)
    utils_controller(DbConn, transport)
    sync_files_controller(DbConn, transport)
    host_files_controller(DbConn, transport)
    hosts_controller(DbConn, transport)

def paginate(q, page, attrs=None, page_size=200):
    '''Paginate results of query'''
    if attrs is None:
        attrs = []
    q=q.limit(page_size).offset(page_size*page)
    return [f.to_dict(*attrs) for f in q]

def tox_auth_controller(DbConn, tox):
    '''
        Manage authentication of tox friends
    '''
    sessions = tox.sessions
    router = tox.router
    actions = tox.actions
    sync_id = tox.sync_id

    def _put_host(db, sync_id, pk, device_name):
        host = db.query(Host).filter(
            Host.pubkey==pk, 
            Host.sync_id==sync_id).first() 
        if not host:
            host = Host(pubkey=pk, sync_id=sync_id, device_name=dname)
            db.add(host)
            db.commit()
        sessions.put(pk, 'host', host)
        return host

    @actions.responds_to('add_primary')
    def _do_add_primary(event):
        if tox.primary.get_address() not in tox.get_friendlist():
            tox.primary.add_friend_norequest(tox.get_address())
        if tox.get_address() not in tox.primary.get_friendlist():
            tox.add_friend_norequest(tox.primary.get_address())
    
    @actions.responds_to('handshake')
    def _do_handshake(action_event):
        '''
            Authenticate in both directions
        '''
        def _do_auth(event):
            '''
                We already sent a nonce
                - recv passwd_hash
                - authenticate
                - if auth then send passwd_hash
            '''
            session1 = sessions.get_session(fid=event.val('fid'))
            session2 = sessions.get_session(addr=addr)
            assert session1 == session2
            peer_nonce = event.val('nonce')
            phash = session.get_hash(peer_nonce)
            
            if not session.authenticate(event.val('passwd_hash')):
                action_event.reply('handshake: peer auth fail')
                return 
            params = {'passwd_hash': phash}
            tox.send('create_session', addr=addr,
                data=params, reply=_check_auth)  
        
        def _check_auth(event):
            '''
               We sent auth, see if it worked
               - add host if worked
            '''
            if event.status != 'ok':
                action_event.reply('handshake: self auth fail')
                return
            action_event.reply('ok')
        addr=action_event.val('addr')
        session = sessions.get_session(addr=addr)
        params = {'nonce': session.nonce}
        tox.send('new_session', addr=addr, reply=_do_auth, data=params)
 
    @router.responds_to('new_session')
    def _cmd_new_session(event):
        session = sessions.get_session(fid=event.val('fid'))
        event.reply('ok', {'nonce': session.nonce, 
            'passwd_hash': session.get_hash(event.val('nonce'))})

    @router.responds_to('create_session')
    def _cmd_create_session(event):
        session = sessions.get_session(fid=event.val('fid'))
        dname = 'nyr' #event.val('device_name', 'unknown')
        if not session.authenticate(event.val('passwd_hash')):
            event.reply('auth fail')
            return
        event.reply('ok')
    
def utils_controller(DbConn, transport):
    router = transport.router
    
    @transport.actions.responds_to('ping')
    def _action_ping(event):
        transport.send('ping', addr=event.val('addr'))

    @transport.router.responds_to('ping')
    def _cmd_ping(event):
        event.reply('pong')

    @transport.router.responds_to('pong')
    def _cmd_pong(event):
        log.info('Pong received')

file_params = ['id', 'file_hash', 'file_size', 'is_dir',
    'rel_path', 'does_exist', 'version', 'ver_data', 'updated_at']

@controller_requires_auth
def sync_files_controller(DbConn, transport):
    '''
        limit access:
        - transport has sync
        - session can store
    '''
    router = transport.router
    sessions = transport.sessions
    sync_id = transport.sync_id
    
    @router.responds_to('get_last_changed')
    def __cmd_get_last_changed(event):
        last = views.sync_last_changed(db, sync_id)
        event.reply('ok', {'last_changed': last})

    @router.responds_to('get_sync_file')
    def _cmd_get_sync_file(event):
        ''' Handle get sync file command '''
        sync_file_id = int(event.val('sync_file_id'))
        sync_file = db.query(SyncFile).filter(
            SyncFile.sync_id == sync_id,
            SyncFile.id == sync_file_id).first()
        if sync_file:
            event.reply('ok', sync_file.to_dict(*file_params))
        else:
            event.reply('not found')
    
    @router.responds_to('list_sync_files')
    def _cmd_list_sync_files(event):
        ''' Get many sync files '''
        params = event.allow('page', 'since').val()
        print('params', params)
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        q = db.query(SyncFile).filter(
            SyncFile.sync_id == sync_id,
            SyncFile.updated_at >= since)
        sync_files = paginate(q, page, attrs=file_params)
        event.reply('ok', {'sync_files': sync_files})
 
@controller_requires_auth
def file_parts_controller(DbConn, transport):
    '''
    '''
    router = transport.router
    sessions = transport.sessions
    sync_id = transport.sync_id

    @router.responds_to('last_changed')
    def _cmd_last_changed(event):
        fid = event.val('fid')
        host = sessions.get(fid, 'host') 
        stime, htime = views.last_changed(sync_id, host.id)

    @router.responds_to('list_file_parts')
    def _cmd_list_file_parts(event):
        params = event.allow('sync_file_id', 'page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        id = int(params.get('sync_file_id', 0))
        q = db.query(SyncPart).filter(
            SyncPart.updated_at >= since,
            Sync.id == sync_id)
        if id:
            q.filter(SyncPart.sync_file_id == id)

        file_parts = paginate(q, page)
        event.reply('ok', {'file_parts':file_parts})

@controller_requires_auth
def hosts_controller(DbConn, transport):
    '''
        Manage Actions For Hosts
    '''
    router = transport.router
    sessions = transport.sessions
    sync_id = transport.sync_id

    @router.responds_to('update_host')
    def _cmd_update_host(event):
        ''' Handle put host command '''
        p = event.get('host').require('pubkey', 'device_name').val()
        pubkey = p['pubkey']
        device_name = p['device_name']
        host = db.query(Host).filter(
                Host.sync_id == sync_id,
                Host.pubkey == pubkey).first()
        if not host:
            host = Host(sync_id=sync_id, pubkey=pubkey)
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
            Host.sync_id == sync_id,
            Host.updated_at >= since)
        hosts = paginate(q, page)
        event.reply('ok', {'hosts': hosts})

@controller_requires_auth
def host_files_controller(DbConn, transport):
    '''
        db: Database session
        sync: sync path
        tr: transport
    '''
    router = transport.router
    sessions = transport.sessions
    sync_id = transport.sync_id

    host_file_params = ['rid', 'file_hash', 'file_size', 'is_dir',
        'rel_path', 'does_exist', 'version', 'ver_data']
    
    @router.responds_to('list_host_files')
    def _cmd_list_host_files(event):
        hfi = event.get('host_file_id')
        q = db.query(HostPart).filter(
            HostPart.sync_file_id == id,
            HostPart.updated_at >= since).filter(
            Sync.id == sync_id)
        file_parts = paginate(q, page)


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

