#!/usr/bin/python
import os
from popen2 import popen2
import pyinotify

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

class UnisonConfig():
	root_local = '/home/hattb/sync'
	root_remote = '/home/rainmaker/users/hattb/sync'
	key_path = '/home/hattb/.ssh/id_dsa'
	unison_path = '/usr/bin/unison'
	unison_prf  = 'default.prf'

class FSMon():
	def __init__(self):
		print "FSMon:__init__()"
		self.q = Queue()
		print "FSMon:WatchManager()"
		self.wm = pyinotify.WatchManager()
		self.mask = pyinotify.IN_MODIFY| pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_ACCESS | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM	
		self.notifier = pyinotify.Notifier(self.wm, PTmp(self.q))
		self.cfg = UnisonConfig()
		print "FSMon:adding watch to: "+self.cfg.root_local
		self.wdd = self.wm.add_watch(self.cfg.root_local, self.mask, rec=True, auto_add=True)

	def CheckFS(self):
		print "FSMon:CheckFS()"
		self.notifier.process_events()
		while self.notifier.check_events(0):
			self.notifier.read_events()
	def stop(self):
		print "FSMon:stop()"
		self.notifier.stop()

# combine cookie operations so they get processed together
# filesystemwatcher might handle this differently though
class PTmp(pyinotify.ProcessEvent):
	def __init__(self,event_queue):
			self.q = event_queue
			self.cfg = UnisonConfig()
	def upload(self,event):			
			print 'Got event: '+event.event_name
			path = self.path_convert(event)
			#cmd = self.cfg.unison_path+' '+self.cfg.unison_prf+' -ui text -sshargs "-i '+self.cfg.key_path+'" -path '+path
			print self.cfg.unison_path
			print self.cfg.unison_prf
			print self.cfg.key_path
			print path
			#p = popen2(cmd)
			#retval = p.wait()
	def path_convert(self,event):
		print 'Path: '+event.path
		print 'Name: '+event.name
		path = os.path.join(event.path, event.name)
		path = path.replace(self.cfg.root_local+'/','')
		event.remote_path = path
	def process_IN_CREATE(self, event):
		event.event_name = 'IN_CREATE'
		self.upload( event )
	def process_IN_DELETE(self, event):
		event.event_name = 'IN_DELETE'
		self.upload( event )
	def process_IN_ACCESS(self, event):
		event.event_name = 'IN_ACCESS'
		self.upload( event )
	def process_IN_MOVE_SELF(self, event):
		event.event_name = 'IN_MOVE_SELF'
		self.upload( event )
	def process_IN_MOVED_FROM(self, event):
		event.event_name = 'IN_MOVED_FROM'
		self.upload( event )
	def process_IN_MOVED_TO(self, event):
		event.event_name = 'IN_MOVED_TO'
		self.upload( event )
	def process_IN_MODIFY(self, event):
		event.event_name = 'IN_MODIFY'
		self.upload( event )

def main():
	mon = FSMon()
	while True:
		try:
			mon.notifier.process_events()
			if mon.notifier.check_events():
				mon.notifier.read_events()
		except KeyboardInterrupt:
				mon.notifier.stop()
				break

if __name__ == '__main__':  
    main()
