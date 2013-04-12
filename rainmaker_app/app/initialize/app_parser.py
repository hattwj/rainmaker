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

from rainmaker_app.conf import load
from time import sleep

# prompt user for valid input
def ask(bag,key):
    valid=False
    while valid == False:
        print('')
        if bag.attr_val(key):
            print 'Default: %s' % bag.subst(str(bag.attr_default(key)))  
        ans = raw_input( "%s: " % bag.attr_desc(key) ) or bag.attr_default(key)
        setattr(bag,key,bag.subst(str(ans)))
        valid = bag.attr_validate(key)
    print 'Using: %s' % bag.attr_val(key)
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

    # 
    def __create_with__(self,key,add_help=False):
        self.parser = argparse.ArgumentParser(version='0.0.2',add_help=add_help)
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
        self.args = args
        self.__create_with__('pre')
        
        # look for action, set app settings
        self.opts,rem_args=self.parser.parse_known_args(self.args)
        self.app.log_level = self.opts.log_level
        self.__detect_action__()
        
        # reparse opts
        self.opts = self.parser.parse_args(self.args)
        
        # carry out response to action after init is complete
        self.func=getattr(self,"__%s__" % self.action)
        self.app.callbacks.register('after_init',self.__after_app_init__)
    
    def __after_app_init__(self):
        print '''
Rainmaker info:
\tuser_dir=%r
\taction=%r
\tlog=%r
        ''' % (self.app.rain_dir,self.action,self.app.log_level)
        self.func()

    def __add__(self,key):
        if key not in self.data:
            return
        for arr in self.data[key]['args']:
            self.parser.add_argument(arr[0],**arr[1])
            
    def __add_action__(self,opts):
        getattr(self,"__%s__" % opts[0].action)(opts[1])

    def __auto__(self):
        p_all = self.app.profiles.all()
        p_auto = self.app.profiles.find_by('auto',True,all=True)
        
        print 'Starting rainmaker' 
        print "Found\t %s profiles" % len(p_all)
        print "\t %s with autostart" % len(p_auto)
        if len(p_auto) == 0:
            print '\n'
            self.parser.print_help()
            print '\nNothing to do. Please create a profile'
            return

        self.app.loop.start(p_auto)

    # create a new profile
    def __create__(self):
        profile = self.app.profiles.new(self.opts.type)
        if self.opts.type in self.data[self.action]['questions']:
            qs=self.data[self.action]['questions'][self.opts.type]
        else:
            qs = profile.attrs.keys()
        
        print 'Creating %s profile\n' % profile.type
        # ask questions
        for v in qs:
            ask(profile,v)         
        profile.save()

    def __delete__(self):
        if not self.opts.title:
            print 'Profile title required...'
            self.__list__()
            return
        
        profile=self.app.profiles.find_by('title',self.opts.title)
        if not profile:
            print 'No profile found with title="%s"' % self.opts.title
            return
        print 'Deleting: %s' % profile.path
        profile.delete()

    def __update__(self):
        profile = self.app.profiles.find_by('title',self.opts.title)
        if not profile:
            print 'No profile found with title=%r' % self.opts.title
            return
        for attr in profile.attrs_dump().keys():
            self.parser.add_argument('--%s'%attr,help=profile.attr_desc(attr))
        self.profile = profile
    
    def __find_profile__(self):
        profile = None
        if hasattr(self.opts,'n') and self.opts.n:
            profiles = self.app.profiles.all()
            n = int(self.opts.n)-1
            if len(profiles) <= n or n < 0:
                print "Profile number %s doesn't exist" % str(n+1)
            else:
                profile = profiles[n]
        elif hasattr(self.opts,'title') and self.opts.title:
            profile = self.app.profiles.find_by('title',self.opts.title)
            if not profile:
                print "Profile titled  %s doesn't exist" % str(self.opts.title)
        elif hasattr(self.opts,'profile_paths') and self.opts.profile_paths:
            pass             
        return profile

    def __list__(self):
        print self.opts
        profile = self.__find_profile__()
        
        if profile:
            for k,v in profile.attrs_dump_key('val').iteritems():
                print '#%s\n%s=%s\n' % (profile.attr_desc(k),k,v)
            return

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
        if not self.opts.title:
            print 'Profile title required...'
            self.__list__()
            return
    
    def __stop__(self):
        if not self.opts.title:
            print 'Profile title required...'
            self.__list__()
            return

    def __info__(self):
        pass
    
    def __status__(self):
        pass
