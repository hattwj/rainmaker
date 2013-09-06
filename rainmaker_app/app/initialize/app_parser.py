#!/usr/bin/python
"""
This file is part of Rainmaker.

    Rainmaker is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Rainmaker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Rainmaker.  If not, see <http://www.gnu.org/licenses/>.
"""
from os.path import basename
from sys import argv, exit
import argparse

from rainmaker_app.lib.conf import load, t
from rainmaker_app.lib import logger
from time import sleep

# prompt user for valid input
def ask(bag,key):
    valid=False
    while valid == False:
        print('')
        if bag.attr_val(key):
            default = bag.subst(str(bag.attr_default(key)))  
        ans = raw_input( "%s [enter=%s]: " % (bag.attr_desc(key),default) ) or bag.attr_default(key)
        setattr(bag,key,bag.subst(str(ans)))
        valid = bag.attr_validate(key)
    #print 'Using: %s' % bag.attr_val(key)
    return ans

class AppParser(object):

    # initialize command line parser
    def __init__(self,app):
        self.data=load('parser.yml')
        self.actions = self.data['auto']['args'][0][1]['choices']
        self.action = None
        self.opts=None
        self.func=None
        self.app = app

    def __create_with__(self,key,add_help=False):
        ''' '''
        self.parser = argparse.ArgumentParser(
            add_help=add_help,
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.__add__(key)
        self.__add__('base')
    
    def __detect_action__(self):
        if not hasattr(self.opts,'action') or self.opts.action==None:
            self.opts.action='auto'
        for v in self.actions:
            if v.startswith(self.opts.action):
                self.action = v
                break

        self.__create_with__(self.action,add_help=True)
    
    # parse cli args and run action
    def parse_args(self,args=None):
        ''' '''
        # create parser
        self.args = args
        self.__create_with__('pre')
        
        # look for action, set app settings
        self.opts,rem_args=self.parser.parse_known_args(self.args)
        logger.log_level = self.opts.log_level
        logger.set_verbosity( self.opts.verbosity )
        self.__detect_action__()
        
        # reparse opts
        self.opts = self.parser.parse_args(self.args)
        
        self.app.set_user_dir(self.opts.user_dir)

        # carry out response to action after init is complete
        self.func=getattr(self,"__%s__" % self.action)
        self.app.callbacks.register('after_init',self.__after_app_init__)
    
    def __after_app_init__(self):
        ''' Run action '''
        self.func()

    def __add__(self,key):
        if key not in self.data:
            return
        for arr in self.data[key]['args']:
            kwargs = arr[1]
            kwargs['help'] = t('parser.help.%s.%s' % (key,arr[0]))
            self.parser.add_argument(arr[0],**kwargs)
            
    def __add_action__(self,opts):
        getattr(self,"__%s__" % opts[0].action)(opts[1])

    def __auto__(self):
        p_all = self.app.profiles.all()
        p_auto = self.app.profiles.find_by('auto',True,all=True)
        
        opts={'count_all':str(len(p_all)),'count_auto':str(len(p_auto))}
          
        print t('parser.action.auto',opts)

        if len(p_auto) == 0:
            print t('parser.notice.nothing_to_do')
            return
        
        for p in p_auto:
            print t('parser.action.start_profile', p.attrs_dump() )
        self.app.loop.start(p_auto)
    
    def __daemon__(self):
        pass

    # create a new profile
    def __create__(self):
        profile = self.app.profiles.new(self.opts.type)
        
        # load a list of questions to ask 
        qs = profile.required_fields
        pattrs = profile.attrs_dump() 
        print t('parser.action.new',{'profile':pattrs},['profile'])
        # ask questions
        for v in qs:
            ask(profile,v)         
        profile.save()
        create_msg = 'parser.action.created.%s' % (self.opts.type)
        print t(create_msg,{'profile':pattrs},['profile'])

    def __delete__(self):
        profiles = self.__find_profiles__()
        if not profiles:
            print t('parser.notice.profile_info_required')
            exit(2)
        for p in profiles:
            profile.delete()

    def __update__(self):
        profile = self.app.profiles.find_by('title',self.opts.title)
        if not profile:
            print t('parser.notice.title_not_found',{'title': self.opts.title})
            return
        for attr in profile.attrs_dump().keys():
            self.parser.add_argument('--%s'%attr,help=profile.attr_desc(attr))
        self.profile = profile
    
    def __find_profiles__(self):
        profiles = []
        if hasattr(self.opts,'n') and self.opts.n:
            all_profiles = self.app.profiles.all()
            n = int(self.opts.n)-1
            if len(profiles) <= n or n < 0:
                print t('parser.notice.number_not_found',{'number': str(n+1) })
            else:
                profiles.append( all_profiles[n] )
        elif hasattr(self.opts,'title') and self.opts.title:
            profile = self.app.profiles.find_by('title',self.opts.title)
            if not profile:
                print t('parser.notice.title_not_found',{'title': self.opts.title})
            else:
                profiles.append(profile)
        elif hasattr(self.opts,'profile_paths') and self.opts.profile_paths:
            profiles += self.app.profiles.load_paths(self.opts.profile_paths)       
        return profiles

    def __list__(self):
        profiles = self.__find_profiles__()
        if not profiles: 
            profiles = self.app.profiles.all()
        print 'Found %s profiles' % len(profiles)
        if len(profiles) == 0:
            return
        print "No.\tTitle\tType\tFilename"
        i=0
        for p in profiles:
            print "%s\t%s\t%s\t%s" % (i+1, p.title, p.type,basename(str(p.path)))
            i+=1
    
    def __start__(self):
        profiles = self.__find_profiles__()
        if not profiles:
            print t('parser.notice.profile_info_required')
            exit(2)
        print t('parser.action.profile_count',{'count':len(profiles)})
        for p in profiles:
            print t('parser.action.start_profile',{'profile':p.attrs_dump()},['profile'])
        self.app.loop.start(profiles)
    
    def __info__(self):
        print t('parser.action.info',{'app':self.app.attrs_dump()})
        self.__list__()
            
    def __status__(self):
        pass
