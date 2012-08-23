import os
import sys
import copy
from watcher import *
import argparse

def ask(q):
    valid=False
    while valid == False:
        print('')
        if q['val']:
            print('Default: '+str(q['val']) ) 
        q['val']=raw_input( q['desc']+': ' ) or q['val']
        valid = validate(q)
    if q['type']=='localpath':
        q['val']=os.path.expanduser(q['val'])
    return q

def validate(q):
    if q['type']=='str':
        return len(str(q['val'] or ''))>0
    elif q['type']=='int':
        return 65536>=int(q['val'])>0

    elif q['type']=='host':
        return len(str(q['val']))>0

    elif q['type']=='localpath':
        return len(str(q['val']))>0

    else:
        return False

def update_profile(conf,args):
    profile=conf.profiles[args.update_profile]
    did_update=False
    for attr, val in vars(args).items():
        if not val:
            continue
        if attr.startswith('update_var_'):
            attr=attr.replace('update_var_','')
            
        if attr.startswith('str_'):
            attr=attr.replace('str_','')
            profile[attr]=str(val)
        elif attr.startswith('int_'):
            attr=attr.replace('int_','')
            profile[attr]=int(val)
        elif attr.startswith('bool_'):
            attr=attr.replace('bool_','')
            if val.lower() == 'true' or val.lower() == 't' or val == '1':
                val=True    
            elif val.lower() == 'false' or val.lower() == 'f' or val == '0':
                val=False
            else:
                print 'Error: %s not bool %s' % (attr,val)
                continue
            profile[attr]=bool(val)
        else:
            print 'bad var %s %s' % (attr,val)
            continue
        did_update=True
    if did_update:
        print 'Saved changes'
        conf.save_profiles() 
    
    print profile

def create_profile(conf,args):
    qkeys=['title','user','local_root','max_backups',
        'ssh_key_path','port','address','remote_path']
            
    profile = conf.templates['unison']

    for attr,val in vars(args).items():
        if attr.startswith('create_var_') and val:
            attr=attr.replace('create_var_','')
            profile[attr]=val
            if attr in qkeys:
                qkeys.pop( qkeys.index(attr) )

    unison_path=conf.find('unison_default.prf')
    f=open(unison_path,'r')
    unison_prf = f.read()
    f.close()
    
    # eval defaults and set the val keys
    profile.set_default()
    
    # ask 
    for key  in qkeys:
        q=profile.meta(key) 
        if not args.quiet:
            q = ask(q)
            print 'Using: '+str(q['val'])+"\n"
            profile[key]=q['val']
        
        if key == 'user':
            profile['remote_path'] = profile.subst(profile['remote_path'])

        answered=False

    while True:
        if args.quiet or not profile['title'] in conf.profiles:
            break

        ans=raw_input('Profile: "%s" already exists. Overwrite y/n ' % profile['title']).lower()
        
        if ans=='y' or ans == 'yes':
            break
        elif ans == 'n' or ans == 'no':
            ask(profile.meta('title'))

    # unison prf file alter: do string subst
    unison_prf=profile.subst(unison_prf)
    
    # set path for unison profile
    prf_f = profile['prf'] = profile['title']
    prf=os.path.abspath( os.path.join(conf.unison_dir,prf_f+'.prf') )
    
    # create seperate unison prf file 
    f = open(prf,'w')
    f.write(unison_prf)
    f.close()
    
    # create profile
    uconf=conf.templates['unison']
    conf.profiles[prf_f]=profile
    conf.save_profiles()

log_levels = {
    'warn':logging.WARN,
    'info':logging.INFO,
    'debug':logging.DEBUG,
    False: logging.WARN 
}

conf=RainmakerConfig()


parser = argparse.ArgumentParser(version='0.1',add_help=True)
parser.add_argument('-d','--delete', action="append", dest='del_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('--start', action="append", dest='start_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('--stop', action="append", dest='stop_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('-t','--test', action="append", dest='test_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('-a','--auto', action="store_true", dest='auto_start', default=True)
parser.add_argument('-q','--quiet', action="store_true", dest='quiet',default=False)
parser.add_argument('--log', action="store", dest='log_level', choices=log_levels.keys(), default='warn')

# profile error?
perr=None

if not '-c' in sys.argv:
    parser.add_argument('-c', action="store_true",default=False,dest='create', help='[TYPE] [OPTIONS]')

else:
    idx = sys.argv.index('-c')
    
    template='unison'
    if len(sys.argv) >= idx + 2 and sys.argv[idx+1][0] != '-':
        if sys.argv[idx+1] in conf.templates:
            template=sys.argv[idx+1]
        else:
            perr = 'Unknown profile type: %s' % sys.argv[idx+1]
        parser.add_argument('-c', action="store",dest='create',default=template, choices=conf['templates'].keys())

    else:
        parser.add_argument('-c', action="store_true",default=False,dest='create', help='[TYPE] [OPTIONS]')
    
    if not perr:
        group=parser.add_argument_group('-c [TYPE=%s] [[OPTIONS]]' % template)
       
        # options
        opts = conf.templates[template]
        for key in opts:
            q=opts.meta(key)['desc']
            group.add_argument('--'+key, action="store", dest='create_var_%s' %key,help=q)

if not '-l' in sys.argv:
    parser.add_argument('-l', action="store_true",default=False,dest='list', help='List all profiles or list settings for specicific profile')

else:
    idx = sys.argv.index('-l')
    
    if len(sys.argv) >= idx + 2 and sys.argv[idx+1][0] != '-':
        parser.add_argument('-l', action="store",dest='list', choices=conf.profiles.keys(), help='List profile settings' )

    else:
        parser.add_argument('-l', action="store_true",default=False,dest='list', help='List all profiles or list settings for specicific profile')
    

if not '-u' in sys.argv:
    idx=None
else:
    idx = sys.argv.index('-u')
if not idx:
    parser.add_argument('-u', action="store",default=False,dest='update_profile',metavar='[PROFILE]', help='[PROFILE] [OPTIONS]')
else:
    if len(sys.argv) >= idx + 2 and sys.argv[idx+1] in conf.profiles:
        
        parser.add_argument('-u', action="store",dest='update_profile',metavar='PROFILE',default=None)
        profile=sys.argv[idx+1]

        group=parser.add_argument_group('-u [PROFILE=%s] [[OPTIONS]]' % profile)
        profile_data = conf.profiles[profile]
        for key in profile_data:
            if isinstance(profile_data[key],str):
                group.add_argument('--'+key, action="store", dest='update_var_str_%s' % key, help=str(profile_data[key]))
            elif isinstance(profile_data[key],bool):
                group.add_argument('--'+key, action="store", dest='update_var_bool_%s' % key, help=str(profile_data[key]))
            elif isinstance(profile_data[key],int):
                group.add_argument('--'+key, action="store", dest='update_var_int_%s' % key, help=str(profile_data[key]))

    else:
        perr = 'Unknown profile'
        parser.add_argument('-u', action="store",default=False,dest='update_profile',metavar='[PROFILE]', help='[PROFILE] [OPTIONS]')

# process cli args
args = parser.parse_args()

#########
# logging
logger=RainmakerUtils.create_logger('main')

print args

######
#error
if perr:
    print perr
    sys.exit()

#####
#List
if args.list==True:
    print 'Profiles: '
    if len(conf.profiles)==0:
        print "\t[None]"
    for key in conf.profiles:
        print "\t%s" % key
    sys.exit()

elif args.list in conf.profiles.keys():
    print 'Profile: %s' % args.list
    for key in conf.profiles[args.list]:
        print "\t%s: %s" % ( str(key), str(conf.profiles[args.list][key]) )
    sys.exit()

elif args.list:
    print 'Unkown profile: %s' % str(args.list)

#######
#Update
if args.update_profile:
    update_profile(conf,args)
    sys.exit()

#######
#Delete
if len(args.del_profiles)>0:
    did_delete=False
    for arg in args.del_profiles:
                
        if arg in conf.profiles:

            p=conf.profiles.pop(arg)
            do_prf_del=p['profile_type']=='rainmaker_unison'

            if do_prf_del:
                path =  os.path.join(conf.unison_dir, '%s.prf' % p['prf'] )
                if os.path.isfile(path):
                    print 'Deleting file: %s' % path
                    os.remove(path)
                else:
                    print 'Error: unable to delete unison profile - %s' % path
            did_delete=True
            print 'Removed profile: %s' % arg
        else:
            print 'Unknown profile: %s' % arg

        if did_delete:
            conf.save_profiles()
            print 'Changes saved'
        else:
            print 'No changes to save'
    sys.exit()

#######
#Create
if args.create:
    create_profile(conf,args)
    sys.exit()

######
#Start

if not args.auto_start:
    #start service with no active profiles
    logger.info('Starting with no profiles')

try:

    rain = Rainmaker(conf,args.auto_start)
    for i in args.start_profiles:
        logger.info("Starting profile:\t%s" % i)
        rain.add_watch(i)

    while True:
        time.sleep(2)
        msgs=  rain.messages()
        if msgs:
            logging.info(msgs)
except KeyboardInterrupt:
    rain.shutdown()

