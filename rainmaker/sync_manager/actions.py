from rainmaker.sync_manager.resolver import resolve_syncs
from rainmaker.db.views import host_last_changed
from rainmaker.db.main import HostFile, file_params


def sync_with_host(db, host, send):
    params = {'since': 0, 'page': 0, 'before': 0}

    def _start():
        htime = host_last_changed(db, host.id)
        params['since'] = htime
        send('get_last_changed', reply=_get_last_changed)

    def _get_last_changed(event):
        params['before'] = event.val('last_changed')
        send('list_sync_files', params, reply=_recv_files)

    def _recv_files(event):
        # get array of params as array of dictionaries
        sf_params =  event.aget('sync_files').require(*file_params).val()
        recv_sync_files(db, host, sf_params)
         
        if sf_params:
            params['page'] += 1
            send('list_sync_files', params, reply=_recv_files)
        else:
            params['page'] = 0
            _reply()

    _start()

def recv_sync_files(db, host, params):
    # convert id to rid
    # map array to dict of dicts
    sdict = {}
    for p in params:
        v = p.pop('id')
        p['rid'] = v
        p['host_id'] = host.id
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

