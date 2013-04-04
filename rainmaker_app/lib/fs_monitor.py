# Queue imports for different python versions
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

# Watchdog
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemMovedEvent

class ProfileEventHandler(FileSystemEventHandler):

    def __init__(self, profile):
        super(FileSystemEventHandler,self).__init__()
        self.cmd_q = Queue()
        self.threads_q = Queue()
        self.profile = profile
        self.log = logger.create('eh_%s' % profile.name)

        # Fill out nested macros (max 5 levels deep)
        for i in range(1,5):
            found_macro = False
            for flag in self.profile['cmd_macros']:
                new_macro = self.do_macro(self.profile['cmd_macros'][flag])
                if self.profile['cmd_macros'][flag] != new_macro:
                    found_macro = True
            if not found_macro:
                break

        # Add macros to commands
        for cmd_key,cmd_val in self.profile['cmds'].items():
            # process command list
            if isinstance(cmd_val, list): 
                for idx,item in enumerate(cmd_val):
                    self.profile['cmds'][cmd_key][idx]=self.do_macro(item)
            # process single command
            else:
                self.profile['cmds'][cmd_key] = self.do_macro(cmd_val)

        self.running = True
        self.start_threads()

    def start_threads(self):
        target = self.cmd_worker
        for i in range( int(self.profile.max_threads) ):
            t = Thread(target=target)
            t.daemon = True
            t.start()
            self.threads_q.put( t )

    # Thread to run command queue
    def cmd_worker(self):
        while self.running==True:
            try:
                cmd =  self.cmd_q.get_nowait()
            except Empty:
                time.sleep(1)
                continue
            self.log.info('exec cmd: %s' % cmd)
            s_cmd = shlex.split(cmd) 
            
            p = Popen(s_cmd,stderr=PIPE, stdout=PIPE)
            result = {  'stdout':p.stdout.read(),
                        'stderr':p.stderr.read(),
                        'returncode':p.returncode,
                        'cmd':cmd
                     }
            self.msg_q.put( result )
            self.log.debug('finished cmd: %s' % cmd)
    
    def matches_any_regex(self,val, regexes):
        for r in regexes:
            m = r.match(val)
            if m: return m
        return False

    """EventHandler"""
    def cmd_create(self, event):

        path=event.src_path
        # Check for paths to ignore
        if self.matches_any_regex(path,self.profile.ignore_paths):
            self.log.info('Ignoring Path: %s : %s' % (event.event_type, path))
            return
        
        self.log.debug('event fired: %s' % event.event_type)

        #Start building command
        if self.profile.use_cmd_all and event.event_type != 'startup':
            cmd = self.profile.cmds_all
        else:
            cmd = self.profile.cmds[event.event_type]
        
        # use base if none exists 
        if cmd == '' or cmd is None:
            self.log.debug( 'no command for event: %s' % event.event_type)
            return
        
        # process command list
        if isinstance(cmd, list): 
            for item in cmd:
                self.do_cmd(item,event)
        # process single command
        else:
            self.do_cmd(cmd,event)

    def do_cmd(self,cmd,event):       
        # Insert placeholder values
        cmd = self.profile.subst(cmd)
        for key in self.conf['cmd_flags']:
            flag = self.conf['cmd_flags'][key]
            if cmd.find( flag ) != -1:
                cmd = cmd.replace( flag , getattr(self, key )(event) )
        # Add command to command queue
        self.cmd_q.put(cmd)

    # scan a command for macros and substitute them
    def do_macro(self,cmd):
        if str(cmd) == '' or cmd is None:
            return ''
        for flag in self.profile['cmd_macros']:
            val = self.profile['cmd_macros'][flag]
            if cmd.find( flag ) != -1:
                cmd = cmd.replace( flag , val )
        return cmd
            
    """ Available client methods """
    def stop(self):
        self.log.info( 'stopping threads' )
        self.running = False
        while True:
            try:
                t =  self.threads_q.get_nowait()
                self.log.info('Stopping thread: %s' % t.name)
                t.join()
            except Empty:
                break
             
    def startup_cmd(self):
        event =FileSystemEvent('startup',self.profile['local_root'],True)
        self.cmd_create(event)

    """ File System Events """
    def on_moved(self, event):
        self.cmd_create(event)

    def on_created(self, event):
        self.cmd_create(event)

    def on_deleted(self, event):
        self.cmd_create(event)

    def on_modified(self, event):
		self.cmd_create(event)

    """ Available Event properties """
    def root(self,event):
        return self.profile['local_root'] 
    
    def src_dir_full(self,event):
        return quote( event.src_path )

    # return event file path relative to root
    def src_file_rel(self,event):
        return event.src_path.replace(self.profile['local_root']+os.sep,'')  

    def dest_file_rel(self,event):
        return event.dest_path.replace(self.profile['local_root']+os.sep,'')  

    def event_type(self,event):
        return event.event_type

class FsMonitor(object):
   
    def __init__(self):
        self.log=logger.create('main')
        self.event_handlers = []
        self.profiles = {}
        self.msg_q = Queue()
        self.observer = Observer()
        self.observer.start()

    def auto_start(self):
        for k in self.profiles:
            if self.profiles[k].auto_start==True:
                self.add_watch(k)

        if not self.event_handlers:            
            self.log.warn('No running profiles')

    def add_watch(self,key):
        if not key in self.profiles:
            self.log.error('Unknown profile %s' % key)
            return

        self.log.info('Starting profile: %s' % key)
        profile = self.profiles[key]
        profile.subst_all()

        if not os.path.isdir(profile.local_root):
            self.log.error('local dir doesnt exist: %s' % profile.local_root)
            return     
        event_handler = RainmakerEventHandler()
        event_handler.init2( self.config, profile, self.msg_q, key )
        self.event_handlers.append( event_handler )

        self.observer.schedule( event_handler, profile.local_root, recursive = profile.recursive) 
        logging.info('Started profile: %s' % key) 
        profile.callbacks.trigger('fs_startup')

    def remove_watch(self, name=None, shutdown=False):
        for i,eh in enumerate(self.event_handlers):
            if eh.name == name or shutdown==True:
                self.event_handlers.pop(i)
                self.log.info('Stopping profile: %s' % k)
                self.observer.unschedule(eh)
                eh.stop()
                if shutdown == False:
                    break

    def shutdown(self):
        self.log.info( "Shutting down...")
        self.observer.stop()
        self.log.info("Shutting down thread and fork pool")
        self.remove_watch(shutdown=True)
        self.observer.unschedule_all()
        self.observer.join()

