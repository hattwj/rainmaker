"""

"""
#For Starting up a subprocess
from __future__ import print_function
import sys
from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

import time
import sys
import os
import atexit

"""#THIS WORKS IN WINDOWS, TEST IN LINUX
from __future__ import print_function
import sys
from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
q = Queue()
t = Thread(target=enqueue_output, args=(p.stdout, q))
t.daemon = True # thread dies with the program
t.start()

# ... do other things here

# read line without blocking
try:  line = q.get_nowait() # or q.get(timeout=.1)
except Empty:
    print('no output yet')
else: # got line
    print(line, end='')
"""
class singleton():
    def __init__(self,sp_path,lock_path):
        self.ON_POSIX = 'posix' in sys.builtin_module_names
        #Default to create a subprocess - B/C Python returns 0 for dead subprocesses (and None for live ones)
        self.sp_poll   = 0
        #Path to the executable that we are going to run
        self.sp_path   = sp_path
        #Default value for created process
        self.isAlive   = True
        #Where we store the lock file for the singleton
        self.lock_path = lock_path
        #Register function to run at exit
        atexit.register(self.Kill)
    def enqueue_output(self,out, queue):
        for line in iter(out.readline, ''):
            queue.put(line)
        out.close()
    def Get_AppData_Path(self):
        return getpath.appdata_path()
    def Lock(self):
        self.lock_time = time.time()
        try:
            file = open(self.lock_path,'w')
        except:#Try again
            time.sleep(2)
            file = open(self.lock_path,'w')
        file.write(str(self.lock_time)+'\n')
        file.flush()
        file.close()
    def Read(self):
        try:
            line = self.q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            line = None
        return line
    def IsLocked(self):
        # Set the Default
        result = False
        #Try to read the lock file
        try:
            file = open(self.lock_path,'r+')
            if file.readline() == str(self.lock_time)+'\n' and self.isAlive==True:
                result = True
            file.close()
        except:
            pass #leave result at False
        return result
    def Stop(self):
        self.isAlive = False
    def Kill(self):
        try:
            self.subproc.kill()
        except:
            pass #Not shure how this happens, but the program choked when trying to die.
    def IsRunning(self):
        result = False
        #Update the process status for the next loop
        self.sp_poll = self.subproc.poll()
        if self.sp_poll == None:
            result = True
        return result
    def Run(self):
        #Check to make sure the proggy is not alive
        if self.sp_poll!=None:
            #Start it if its dead
            self.subproc = Popen([self.sp_path], stdout=PIPE, bufsize=1, close_fds=self.ON_POSIX)
            self.q = Queue()
            self.t = Thread(target=self.enqueue_output, args=(self.subproc.stdout, self.q))
            self.t.daemon = True # thread dies with the program
            self.t.start()
        if self.IsRunning():
            self.Lock()

