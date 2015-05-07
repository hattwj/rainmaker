from sqlalchemy.orm import subqueryload, joinedload
from rainmaker.net.sessions import controller_requires_auth
from rainmaker.db.main import Sync, SyncFile, Host, HostFile
from rainmaker.db import views

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
    'rel_path', 'does_exist', 'version', 'ver_data', 'updated_at']

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
    
    @router.responds_to('get_last_changed')
    def __cmd_get_last_changed(event):
        last = views.sync_last_changed(db, sync.id)
        event.reply('ok', {'last_changed': last})

    @router.responds_to('get_sync_file')
    def _cmd_get_sync_file(event):
        ''' Handle get sync file command '''
        sync_file_id = int(event.val('sync_file_id'))
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
        sync_files = paginate(q, page, attrs=file_params)
        event.reply('ok', {'sync_files':sync_files})
 
@controller_requires_auth
def file_parts_controller(db, transport):
    '''
    '''
    router = transport.router
    sessions = transport.sessions
    sync = transport.sync

    @router.responds_to('last_changed')
    def _cmd_last_changed(event):
        fid = event.val('fid')
        host = sessions.get(fid, 'host') 
        stime, htime = views.last_changed(sync.id, host.id)

    @router.responds_to('list_file_parts')
    def _cmd_list_file_parts(event):
        params = event.allow('sync_file_id', 'page', 'since').val()
        since = int(params.get('since', 0))
        page = int(params.get('page', 0))
        id = int(params.get('sync_file_id', 0))
        q = db.query(SyncPart).filter(
            SyncPart.updated_at >= since,
            Sync.id == sync.id)
        if id:
            q.filter(SyncPart.sync_file_id == id)

        file_parts = paginate(q, page)
        event.reply('ok', {'file_parts':file_parts})

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

from pytox import Tox
from threading import Thread, Lock
from time import sleep
from concurrent.futures import ThreadPoolExecutor


class FileTransfers():
    def __init__(self):
        self.tr = {}
    

class FileServer():
    '''
        Threaded file server: 
        - max transfers per application
        - files lock while send/recv
    '''
    MAX_THREADS = 10
    running = False

    def __init__(self):
        self.e_send = ThreadPoolExecutor(max_workers=self.MAX_THREADS)
        self.e_recv = ThreadPoolExecutor(max_workers=self.MAX_THREADS)
        self.transports = {}
        self.running = True
    
    def register_transport(self, tr):
        '''
            Register transport with server
        '''
        def _on_file_send_request(friendId, file_no, file_size, filename):
            '''
                Check to see if file/parts needed
                - does a receiver exist?
                    - accept
            '''
            xfer = self.xfers.find_file(key, friendId, filename)
            if xfer:
                xfer.on_file_send_request(data)
        
        def _on_file_data(friendId, file_no, data):
            '''
                Send data to receiver
            '''
            xfer = self.xfers.get(key, friendId, file_no)
            if xfer:
                xfer.on_file_data(friendId, file_no, data)
        
        def _on_file_control(friendId, receive_send, file_no, ctrl, data):
            '''
                Notify sender/receiver
                - does a xfer exist?
                    - receiver?
                        - data add parts
            '''
            xfer = self.xfers.get(key, friendId, file_no)
            if xfer:
                xfer.on_file_control(ctrl, data)
         
        tr.on_file_send_request = _on_file_send_request
        tr.on_file_data = _on_file_data
        tr.on_file_control = _on_file_control
        key = len(self.transports.keys())        
        self.transports[key] = tr
        return key

    def send(self, tr, fid, sync_file, parts):
        '''
            Send a file
            - register sender to receive file_control events
        '''
        def _send():
            '''
                Control logic goes here
            '''
            try:
                fm.setup()
            except OSError:
                print('Err accessing file')
                return
            while fm.has_parts() and self.running:
                try:
                    fm.send_part()
                except Tox.OperationFailedError:
                    fm.rewind()
                    sleep(1)
                except OSError:
                    print('Read error while sending')
                    break
            fm.tear_down()
        fm = FileSender(tr, fid, sync_file, parts)
        job = self.e_send.submit(_send)
        return job
    
    def download(self, tr, host_file):
        path = os.path.join(host_file.host.sync.path, host_file.rel_path)
        self.path = path + '.part'
        if host_file.is_dir:
            if not os.path.exist(path):
                os.mkdir(path)
                return
        gen_file(path, host_file.file_size)
        with self.lock:
            download = self.downloads.get(sync_file.path)
            if not download:
                download = Download(path, temp_path)
                self.downloads[path] = download
                self.recv(tr, download)

    def recv(self, tr, host_file):
        '''
            Search for senders
            - cancel if none needed
            - wait x seconds for response
        '''
        def _recv():
            pass
        fm = FileReciever(host_file)
        job = self.e_recv.submit(_recv)
        return job

from collections import namedtuple
FileRecStat = namedtuple("FileRecStat", "started complete length part_no data")
XferStat = namedtuple('XferStat', 'recv xfer job record')

class FileReceiver():
    '''
        - DB observer/controller:
            - abort recv on change
            - Check and run resolver on controller signal
            - init recv requests with server
        - FileServer:
            Parameters:
                None
            Methods:
            - transport register
                - forward file control events to... 
                    - DownloadInit
            - manage transfer counts, threadpool
            - init and manage file sends - FileSender
            - init and manage file recs - FileReceiver
                - add parts if new notification comes (db)
            - DownloadInit (new class)
                - handle rec file locks
                    - single file can only have single receiver
                - register receiver with server
                    - lock for file
                    - or return current receiver
                - check for temp file exist
                    - create blank file
                    - or copy existing template file
                - create receiver and return
        Parameters:
            - DownloadManager
        Properties:
            - parts dict of Array/Class/NamedTuple
                - FileRecStat 
                - started, complete, length, part_no, data
        Methods:
        - stop:
            - Stop receiving data
        
        Handlers:
        - on_file_control
            - part complete
                - send to download manager
                - Notify manager if out of parts
            - part_incoming
                - Accept if needed
                - create buffer
        - on_file_data
            - check for buffer
            - buffer piece
    '''
    def __init__(self, tr, host_file, part_stats):
        self.tr = tr
        self.host_file = host_file
        self.part_stats = part_stats

class FileSender():
    '''
        Send parts of this file to host
    '''
    FILE_DONE = '*'

    _offset = None
    _part = None
    _max_part_offset = None

    def __init__(self, tr, fid, sync_file, parts):
        self.tr = tr
        self.fid = fid
        self.sync_file = sync_file
        self.chunk_size = sync_file.chunk_size
        self.parts = sorted(parts)

    def setup(self):
        '''
            Notify that we will send a file
        '''
        self.f = open(self.sync_path.path, 'rb')
        self.file_no = self.tr.new_file_sender(self.fid, self.parts_size(),
            self.sync_path.rel_path)
    
    def parts_size(self):
        '''
            Calculate total amount of data to send
        '''
        lparts = len(self.sync_file.file_parts.data)
        total = 0
        for p in parts:
            if p + 1 == lparts:
                total += self.sync_file.file_size % self.chunk_size
            else:
                total += self.chunk_size
        return total

    def tear_down(self):
        '''
            Send signal that file send complete
        '''
        self.f.close()
        self.tr.file_send_control(self.fid, 0, self.file_no,
            Tox.FILECONTROL_FINISHED, self.FILE_DONE)

    def has_parts(self):
        '''
            Still have parts to send?
        '''
        return len(self.parts) > 0
    
    def part_sent(self, idx):
        '''
            Remove part from list
        '''
        self.parts.remove(idx)

    def send_part(self):
        '''
            Send pieces of part until sent
        '''
        # Signal part to be sent
        part_no = self.parts[0]
        self.tr.file_send_control(self.fid, 0, self.file_no,
                Tox.FILECONTROL_FINISHED, 'start:%s' % part_no)
        # send part
        while True:
            chunk_size = self.tr.file_data_size(self.file_no)
            data = self.get_data(chunk_size, part)
            if not data:
                break
            self.tr.file_send_data(self.fid, self.file_no, data)
        # Signal part send complete
        self.part_sent(part_no)
        self.tr.file_send_control(self.fid, 0, self.file_no,
                Tox.FILECONTROL_FINISHED, 'end:%s' % part_no)

    def get_data(self, chunk_size, part):
        '''
            Get data from a part, increment counters
        '''
        # Adjust offsets if we are at a new part
        if self._part != part:
            self._part = part
            offset = part * self.chunk_size
            self._max_part_offset = offset + self.chunk_size
            if self._max_part_offset > self.sync_file.file_size:
                self._max_part_offset = self.sync_file.file_size
            if offset != self._offset:
                self.f.seek(offset)
            self._last_offset = offset
            self._offset = offset
        # Adjust chunk size
        if chunk_size + self._offset > self._max_part_offset:
            chunk_size = self._max_part_offset - self._offset
        # Bail if nothing to get
        if chunk_size <= 0:
            return None
        # Record offset and read data
        self._last_pos = self._offset
        data = self.f.read(chunk_size)
        self._offset = len(data) + self._offset
        return data
    
    def rewind(self):
        '''
            Rewind to previous offset position
        '''
        if self._last_offset is not None:
            self._offset = self._last_offset
            self.f.seek(self._last_offset)

def files_controller(db, transport):
    recv_files = {}
    send_files = {}
    
    def do_file_senders():
        # Send file data for all requests
        for fileno in send_files.keys():
            rec = send_files[fileno]
            # is file ready to send?
            if not rec.start:
                continue
            try:
                chunk_size = transport.file_data_size(fileno)
                while True:
                    # get part
                    data = rec.read(chunk_size)
                    if len(data):
                        # send part
                        transport.file_send_data(frno, fileno, data)
                    # update sender
                    rec.sent += len(data)
                    
                    # terminate send if done
                    if rec.sent == rec.size:
                        rec.tear_down()
                        transport.file_send_control(frno, 0, fileno,
                                Tox.FILECONTROL_FINISHED)
                        del send_files[fileno]
                        break
            except OperationFailedError as e:
                rec.rewind()

    # move to traditional event
    def on_file_send_request(friendId, file_no, file_size, filename):
        #: TODO: implement some sort of access control
        print("%s tries to upload a file `%s', accepted" %
                (self.get_name(friendId), filename))
        friend_key = self.get_client_id(friendId)
        # Generate receiver
        rec = FileRecord(friendId, filename, file_size, True)
        rec.setup()
        recv_files[file_no] = rec
        # Signal Ready to receive
        transport.file_send_control(friendId, 1, file_no, Tox.FILECONTROL_ACCEPT)

    def on_file_control(friendId, receive_send, file_no, ctrl, data):
        if receive_send == 1 and ctrl == Tox.FILECONTROL_ACCEPT:
            # file requested
            send_files[file_no].setup()
        elif receive_send == 0 and ctrl == Tox.FILECONTROL_FINISHED:
            # we are done receiving this file
            self.recv_files[file_no].tear_down(file_no)
            #filename = self.recv_files[file_no].filename
            #os.rename(filename, filename.rstrip(".part"))
            #del self.recv_files[file_no]

    def on_file_data(friendId, file_no, data):
        rec = self.recv_files.get(file_no)
        if rec:
            rec.write(file_no, data)
            rec.recv += len(data)

    transport.on_file_send_request = on_file_send_request
    transport.on_file_control = on_file_control
    transport.on_file_data = on_file_data

