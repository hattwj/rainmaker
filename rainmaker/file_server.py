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

    # File send complete code
    FILE_DONE = '*'

    # current offset in file (bytes)
    _offset = None
    # current part number being sent
    _part = None
    # maximum part number to be sent
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

#def files_controller(db, transport):
#    recv_files = {}
#    send_files = {}
#    
#    def do_file_senders():
#        # Send file data for all requests
#        for fileno in send_files.keys():
#            rec = send_files[fileno]
#            # is file ready to send?
#            if not rec.start:
#                continue
#            try:
#                chunk_size = transport.file_data_size(fileno)
#                while True:
#                    # get part
#                    data = rec.read(chunk_size)
#                    if len(data):
#                        # send part
#                        transport.file_send_data(frno, fileno, data)
#                    # update sender
#                    rec.sent += len(data)
#                    
#                    # terminate send if done
#                    if rec.sent == rec.size:
#                        rec.tear_down()
#                        transport.file_send_control(frno, 0, fileno,
#                                Tox.FILECONTROL_FINISHED)
#                        del send_files[fileno]
#                        break
#            except OperationFailedError as e:
#                rec.rewind()
#
#    # move to traditional event
#    def on_file_send_request(friendId, file_no, file_size, filename):
#        #: TODO: implement some sort of access control
#        print("%s tries to upload a file `%s', accepted" %
#                (self.get_name(friendId), filename))
#        friend_key = self.get_client_id(friendId)
#        # Generate receiver
#        rec = FileRecord(friendId, filename, file_size, True)
#        rec.setup()
#        recv_files[file_no] = rec
#        # Signal Ready to receive
#        transport.file_send_control(friendId, 1, file_no, Tox.FILECONTROL_ACCEPT)
#
#    def on_file_control(friendId, receive_send, file_no, ctrl, data):
#        if receive_send == 1 and ctrl == Tox.FILECONTROL_ACCEPT:
#            # file requested
#            send_files[file_no].setup()
#        elif receive_send == 0 and ctrl == Tox.FILECONTROL_FINISHED:
#            # we are done receiving this file
#            self.recv_files[file_no].tear_down(file_no)
#            #filename = self.recv_files[file_no].filename
#            #os.rename(filename, filename.rstrip(".part"))
#            #del self.recv_files[file_no]
#
#    def on_file_data(friendId, file_no, data):
#        rec = self.recv_files.get(file_no)
#        if rec:
#            rec.write(file_no, data)
#            rec.recv += len(data)
#
#    transport.on_file_send_request = on_file_send_request
#    transport.on_file_control = on_file_control
#    transport.on_file_data = on_file_data
#
