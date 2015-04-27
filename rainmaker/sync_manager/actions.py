from rainmaker.sync_manager.resolver import resolve_syncs
from rainmaker.db.views import find_last_changed
from rainmaker.db.main import HostFile, file_params

def sync_with_host(db, host, send):
    params = {'since': 0, 'page': 0, 'before': 0}

    def _start():
        stime, htime = find_last_changed(db, host.sync_id, host.id)
        params['since'] = htime
        send('get_last_changed', reply=_get_last_changed)

    def _get_last_changed(event):
        params['before'] = event.val('last_changed')
        send('list_sync_files', params, reply=_recv_files)

    def _recv_files(event):
        # get array of params as array of dictionaries
        sf_params =  event.aget('sync_files').require(*file_params).val()
        for sf in sf_params:
           sf['rid'] = sf.pop('id')
           sf['host_id'] = host.id
           hf = HostFile(**sf)
           host.host_files.append(hf)
         
        if sf_params:
            params['page'] += 1
            send('list_sync_files', params, reply=_recv_files)
        else:
            params['page'] = 0
            send('list_file_parts', params, reply=_recv_parts)
    
    def _recv_parts(event):
        '''
            need sync_file_id to host_file_id convert
        '''
        sync_files = event.val('file_parts')
        recv_sync_files(db, host, sync_files)

        if sync_files:
            params['page'] += 1
            send('list_file_parts', params, reply=_recv_parts)
        else:
            _run_resolver()       
    
    def _run_resolver():
        resolutions = resolve_syncs(host.sync_id, host.id) 
        print(resolutions)

    _start()

def recv_sync_files(db, host, params):
    # convert id to rid
    # map array to dict of dicts
    sdict = {}
    for p in params:
        v = p.pop('id')
        p['rid'] = v
        sdict[v] = p
    # find existing files
    host_files = db.query(HostFile).filter(
        HostFile.rid.in_(sdict.keys()),
        HostFile.host_id == host.id).all()
    # update
    for hf in host_files:
        attrs = sdict.pop(hf.rid)
        hf.update(**attrs)
    # create
    for k, sf in sdict.items():
        hf = HostFile(**sf)
        host.host_files.append(hf)
    # commit
    db.add(host_files)
    db.add(host)
    db.commit()

'''

serialized parts:
    simple update
    some changes to make:
    harder to find multiple peers for parts
        - just find identical files and use only one for info

'''
