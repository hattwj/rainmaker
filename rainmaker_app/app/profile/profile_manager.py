import os
import shlex
from subprocess import PIPE, Popen

from calendar import timegm
from time import gmtime

from rainmaker_app.lib import logger, RegexDict
from .fs_monitor  import FsMonitor
from .log_monitor import LogMonitor

class ProfileManager(object):
    sync_interval = 5
    last_loop = 0
    group_call_template = 'cmd_for_%s_group'
    cmd_call_template = 'cmd_for_%s_event'

    def __init__(self,profile,events_dir):
        profile.attr_subst('guid')
        profile.attr_subst('local_root')
        profile.attr_subst('remote_root')

        fslog_path = os.path.join(events_dir,'%s.log' % profile.guid)
        self.fslog_path = fslog_path
        self.fs_monitor = FsMonitor(profile.local_root,fslog_path,profile.ignore_patterns)
        self.log_monitor = LogMonitor(events_dir,fslog_path)
        
        self.log=logger.create(self.__class__.__name__)
        self.profile = profile
        # create output parser regexes
        self.output_parser = RegexDict( self.profile.output_dict )
    
    def startup(self):
        self.__sync_events__()
        events = self.log_monitor.get_events()
        self.run_cmd(key='startup')

    def get_events(self,all_events=False):
        ''' Process any events that may have occurred '''
        results = []
        now = timegm(gmtime())
        # check for remote events
        if all_events or (self.last_loop + self.sync_interval) - now < 0:
            self.last_loop = timegm(gmtime())
            self.__sync_events__()
            events = self.log_monitor.get_events()
        events += self.fs_monitor.get_events()
        return events

    def run_cmd(self,cmd=None,key=None):
        ''' run command or run contents of key as a command '''
        cmd = self.profile.subst(self.profile.attr_val(key)) if key and key in self.profile.attrs else cmd
        if key and key not in self.profile.attrs:
            raise KeyError('No command: %s' % key)
        if not cmd:
            raise AttributeError('Cant run empty command')
        self.profile.log.debug('Running %s' % cmd)
        s_cmd = shlex.split(cmd) 
        self.profile.log.info('Running command %s',cmd)
        p = Popen(s_cmd, shell=False, stderr=PIPE, stdout=PIPE)
        out = p.communicate()
        result = {  'stdout':out[0],
                    'stderr':out[1],
                    'returncode':p.returncode,
                    'cmd':cmd
                 }
        result['output'] = self.__process_output__(result)
        if result['returncode'] > 0:
            self.profile.log.debug(result)
        self.log.info('Cmd result: %s' % result['output'])
        return result

    # analyze output
    def __process_output__(self,output):
        result=[]
        result += self.output_parser.search(output['stderr'])
        result += self.output_parser.search(output['stdout'])
        if not result:
            result.append('unknown')
            self.log.warn('Unrecognized command output')
            self.log.info(output)
        return result

    def events_to_cmds(self,events):
        ''' Convert events to shell commands '''
        cmds = []
        attrs = self.profile.attrs_dump()
        attrs['events'] = events
        cmds += self.__subst_events_to_commands__(events,attrs)
        return cmds

    # group events in dictionary based on event_type key    
    def __group_events__(self,events):
        ''' Create groups to allow for_each loops in commands '''
        et = 'event_type'
        spr='event_src_path_rel'
        spr_paths = []
        groups = {}

        # add event to group
        for event in events:
            k = event[et]
            spr_c = event[spr]
            
            # Unique paths only
            if spr_c in spr_paths:
                self.log.info('Ignoring duplicate path.')
                continue
            
            if k not in groups:
                groups[k] = []

            groups[k].append(event)
            
            spr_paths.append(spr_c)
        
        return groups

    def __subst_events_to_commands__(self,events,attrs,key='event_type'):
        ''' Convert an array of events into an array of shell commands'''
        cmds = []
        groups = self.__group_events__(events)
        for k,v in groups.iteritems():
            group_call_key = self.group_call_template % k
            cmd_call_key = self.cmd_call_template % k
            if group_call_key in attrs:
                xattrs = dict( attrs.items() + {'events':v}.items() )
                cmds.append( self.profile.subst(attrs[group_call_key], xattrs ) )
            elif cmd_call_key in attrs:
                for event in v:
                    xattrs = dict( attrs.items() + event.items() )
                    cmds.append( self.profile.subst(attrs[cmd_call_key],xattrs) )
            else:
                self.log.warn("No Action specified for %s events" % k)
        return cmds

    def __sync_events__(self):
        ''' sync server side events ''' 
        self.run_cmd(key='cmd_sync_send')
        self.run_cmd(key='cmd_sync_recieve')

