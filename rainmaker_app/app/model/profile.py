from os import remove
from string import Template
from yaml import safe_dump,safe_load
import re

# will move to handler
import shlex
from subprocess import PIPE, Popen

from .base_handler import BaseHandler
from rainmaker_app.lib import RecordHooks
from rainmaker_app.lib import RegexDict
from rainmaker_app.conf import load

class Profile(RecordHooks):

    def __init__(self,data={},vals=None,path=None):
        RecordHooks.__init__(self,'profile')
        self.add_attrs(data)
        self.path=path
        if vals:
            for k,v in vals.iteritems():
                setattr(self,k,v)
        self.group_call_template = 'cmd_for_%s_group'
        self.cmd_call_template = 'cmd_for_%s_event'
        self.callbacks.add('get_events')
        self.callbacks.register('delete',self.on_delete)
        self.callbacks.register('save',self.on_save)
        self.callbacks.register('validate',self.on_validate)

    def on_validate(self, **kwargs):
        return True

    def on_save(self,**kwargs):
        if not self.path:
            return False
        f = open(self.path,'w')
        safe_dump(self.attrs_dump_key('val'), f)
        f.close()
        self.log.info('Changes saved to: %s ' % self.path)
        return True

    def on_delete(self,**kwargs):
        if not self.path:
            return False
        remove(self.path)
        return True

    def on_before_save(self,**kwargs):
        # set guid
        if self.guid == None:
            self.guid = _lib.rand_str(10)
    ##
    # Schedule handler to run in observer
    ##
    def schedule(self,observer):
        self.handler_init()
        observer.schedule( self.handler, self.local_root, recursive = self.recursive) 
        self.observer = observer

    ###
    # Unschedule event handler
    ###
    def unschedule(self):
        self.observer.unschedule(self.handler)

    ###
    # Handle events
    ###
    def handler_init(self):
        if not self.local_root:
            raise AttributeError('local_root must be set')
        # create handler
        kwargs = {
            'ignore_patterns': self.ignore_patterns,
            'path':self.local_root
            }
        self.handler = BaseHandler(**kwargs)

        # create output parser regexes
        self.output_parser = RegexDict( self.output_dict )
        return self.handler

    def process_events(self):
        results = []
        events = self.handler.get_events()
        self.callbacks.trigger('get_events',events=events)
        cmds = self.build_cmds(events)
        return cmds

    def run_cmd(self,cmd=None,key=None):
        cmd = self.subst(self.attr_val(key)) if key and key in self.attrs else cmd
        if key and key not in self.attrs:
            raise KeyError('No command: %s' % key)
        if not cmd:
            raise AttributeError('Cant run empty command')
        self.log.debug('Running %s' % cmd)
        s_cmd = shlex.split(cmd) 
        self.log.info('Running command %s',s_cmd[0])
        p = Popen(s_cmd, shell=False, stderr=PIPE, stdout=PIPE)
        out = p.communicate()
        result = {  'stdout':out[0],
                    'stderr':out[1],
                    'returncode':p.returncode,
                    'cmd':cmd
                 }
        self.log.debug('Finished cmd: %s' % cmd)
        result['output'] = self.process_output(result)
        self.log.debug(result['output'])
        
        return result

    # analyze output
    def process_output(self,output):
        result=[]
        result += self.output_parser.search(output['stderr'])
        result += self.output_parser.search(output['stdout'])
        if not result:
            result.append('unknown')
        self.log.info("Command parse result: %s" % ' '.join(result))
        return result

    def build_cmds(self,events):
        ''' Convert events to shell commands '''
        cmds = []
        attrs = self.attrs_dump()
        attrs['events'] = events

        cmds += self.subst_events_to_commands(events,attrs)
        return cmds

    # group events in dictionary based on event_type key    
    def group_events(self,events):
        ''' Create groups to allow for_each loops in commands '''
        et = 'event_type'
        groups = {}
        # add event to group
        for event in events:
            k = event[et]
            if k not in groups:
                groups[k] = []
            groups[k].append(event) 
        return groups   

    def subst_events_to_commands(self,events,attrs,key='event_type'):
        cmds = []
        groups = self.group_events(events)
        for k,v in groups.iteritems():
            group_call_key = self.group_call_template % k
            cmd_call_key = self.cmd_call_template % k
            if group_call_key in attrs:
                xattrs = dict( attrs.items() + {'events':v}.items() )
                cmds.append( self.subst(attrs[group_call_key], xattrs ) )
            elif cmd_call_key in attrs:
                for event in v:
                    xattrs = dict( attrs.items() + event.items() )
                    cmds.append( self.subst(attrs[cmd_call_key],xattrs) )
            else:
                self.log.warn("No Action specified for %s events" % k)
        return cmds
    
    # return event file path relative to root
    def rel_path(self,path_base,path2):
        return path2.replace(path_base+os.sep,'')
