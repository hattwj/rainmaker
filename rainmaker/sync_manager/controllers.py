from rainmaker.db.main import SyncFile, SyncPart, Host, HostFile, HostPart

def get_sync(session, event):
    pass

def get_host(session, event):
    pass

def utils_controller(session, tr):
    def _cmd_ping(event):
        event.reply('pong')

    def _cmd_pong(event):
        pass

    tr.register('ping', _cmd_ping)
    tr.register('pong', _cmd_pong)

file_params = ['id', 'file_hash', 'file_size', 'is_dir',
    'rel_path', 'does_exist', 'version', 'ver_data']

def sync_files_controller(session, tr):
    '''
        session: Database session
        sync: sync path
        tr: transport
    '''
    
    def _cmd_get_sync_file(event):
        ''' Handle get sync file command '''
        sync_file_id = int(event.val('id'))
        sync_file = session.query(SyncFile).filter(
            SyncFile.sync_id == sync.id,
            SyncFile.id == sync_file_id).first()
        if sync_file:
            event.reply('ok', sync_file.to_dict(*file_params))
        else:
            event.reply('not found')
        
    def _cmd_list_sync_files(event):
        ''' Get many sync files '''
        params = event.allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        q = session.query(SyncFile).filter(
            SyncFile.sync_id == sync.id,
            SyncFile.updated_at >= since)
        sync_files = paginate(q, page)
        event.reply('ok', sync_files)
    
    def _cmd_list_sync_parts(event):
        params = event.require('sync_file_id').allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        id = int(params['sync_file_id'])
        q = session.query(SyncPart).filter(
            SyncPart.sync_file_id == id,
            SyncPart.updated_at >= since)
        sync_parts = paginate(q, page)
        event.reply('ok', sync_parts)

    tr.register('get_sync_file', _cmd_get_sync_file)
    tr.register('list_sync_files', _cmd_list_sync_files)
    tr.register('list_sync_parts', _cmd_list_sync_parts)


def paginate(q, page, attrs=None, page_size=200):
    '''Paginate results of query'''
    if attrs is None:
        attrs = []
    q=q.limit(page_size).offset(page_size*page)
    return [f.to_dict(*attrs) for f in q]

def HostsController(session, tr):
    '''
        Manage Actions For Hosts
    '''
    def _cmd_put_host(event):
        ''' Handle put host command '''
        p = event.get('host').require('pubkey', 'device_name').val()
        pubkey = p['pubkey']
        device_name = p['device_name']
        host = session.query(Host).filter(
                Host.sync_id == sync.id,
                Host.pubkey == pubkey).first()
        if not host:
            host = Host(sync_id=sync.id, pubkey=pubkey)
        host.device_name = device_name
        session.add(host)
        session.commit()
        event.reply('ok')

    def _cmd_list_host(event):
        params = event.allow('page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        q = session.query(Host).filter(
            Host.sync_id == sync.id,
            Host.updated_at >= since)
        hosts = paginate(q, page)
        event.reply('put_hosts', hosts)

    tr.register('put_host', _cmd_put_host)
    tr.register('list_hosts', _cmd_list_host)
    return tr

def HostFilesController(session, tr):
    '''
        session: Database session
        sync: sync path
        tr: transport
    '''
    host_file_params = ['rid', 'file_hash', 'file_size', 'is_dir',
        'rel_path', 'does_exist', 'version', 'ver_data']
    
    def _cmd_put_host_file(event):
        ''' Handle put file command '''
        p = event.get('host_file').require(*host_file_params).val()
        host_file = session.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.rid == p['rid']).first()
        if not host_file:
            host_file = HostFile()
        host_file.update_attributes(**p)
        session.add(host_file)
        session.commit()
        event.reply('ok')

    def _cmd_delete_host_file(event):
        p = event.val('rid')
        host_file = session.query(HostFile).filter(HostFile.rid == rid).first()
        if host_file:
            session.delete(host_file)
            session.commit()
            event.reply('ok')
        else:
            event.reply('not found')

    def _cmd_get_host_file(event):
        ''' Handle get host file command '''
        p = event.val('rid')
        host_file = session.query(HostFile).filter(
            HostFile.host_id == host.id,
            HostFile.id == p['rid']).first()
        if host_file:
            event.reply('put_host_file', host_file.to_dict())
        else:
            event.reply('not found')

    tr.register('put_host_file', _cmd_put_host_file)
    tr.register('delete_host_file', _cmd_delete_host_file)
    tr.register('get_host_file', _cmd_get_host_file)

