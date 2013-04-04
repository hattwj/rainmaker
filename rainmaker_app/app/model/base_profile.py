from os import remove
from string import Template
from yaml import safe_dump
import re

# will move to handler
import shlex
from subprocess import PIPE, Popen

from base_handler import BaseHandler
from lib import RecordHooks
from lib import RegexDict
from conf.model.base_profile import attrs
class BaseProfile(RecordHooks):

    def __init__(self,data=[],path=None):
        RecordHooks.__init__(self,'profile')
        self.add_attrs(attrs)
        self.add_attrs(data)
        self.path=path
        self.group_call_template = 'cmd_for_%s_group'
        self.cmd_call_template = 'cmd_for_%s_event'
        self.callbacks.register('delete',self.on_delete)
        self.callbacks.register('save',self.on_save)
        self.callbacks.register('validate',self.on_validate)

    def on_validate(self, **kwargs):
        return True

    def on_save(self,**kwargs):
        if not self.path:
            return False
        f = open(self.path,'w')
        safe_dump(self.attrs_dump(), f)
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
    
    ###
    # Handle events
    ###
    def handler_init(self):
        # create handler
        kwargs = {
            'ignore_patterns': self.ignore_patterns
            }
        self.handler = BaseHandler(**kwargs)

        # create output parser regexes
        self.output_parser = RegexDict( self.output_dict )

    def process_events(self):
        results = []
        events = self.handler.get_events(self.local_root)
        cmds = self.build_cmds(events)
        return cmds

    def run_cmd(self,cmd):
        self.log.info('Running cmd: %s' % cmd)
        s_cmd = shlex.split(cmd) 
        p = Popen(s_cmd, shell=False, stderr=PIPE, stdout=PIPE)
        out = p.communicate()
        result = {  'stdout':out[0],
                    'stderr':out[1],
                    'returncode':p.returncode,
                    'cmd':cmd
                 }
        self.log.debug('Finished cmd: %s' % cmd)
        return result

    # analyze output
    def process_output(self,output):
        result=[]
        result += self.output_parser.search(output['stderr'])
        result += self.output_parser.search(output['stdout'])
        if not result:
            result.append('unknown')
        self.log.debug("cmd_parse: %s" % ' '.join(result))
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
