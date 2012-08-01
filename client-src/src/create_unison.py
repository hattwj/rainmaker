import os
import sys
import copy
from watcher import *
import argparse

def ask(q):
    valid=False
    while valid == False:
        print('')
        if q['default']:
            print('Default: '+str(q['default']) ) 
        q['ans']=raw_input( q['q']+' ' ) or q['default']
        valid = validate(q)
    return q

def validate(q):
    if q['type']=='str':
        return len(str(q['ans'] or ''))>0
    elif q['type']=='int':
        return 65536>=int(q['ans'])>0

    elif q['type']=='host':
        return len(str(q['ans']))>0

    elif q['type']=='localpath':
        return len(str(q['ans']))>0

    else:
        return False

def do_unison(conf,args):
    questions=conf['questions']['unison']
    qkeys=['title','user','local_root','max_backups',
        'ssh_key_path','port','address','remote_path']
            
    profile = {}
    for q in questions:
        profile[q]=questions[q]['default']

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

    # ask 
    for key  in qkeys:
        if not args.quiet:
            q = ask(questions[key])
            print 'Using: '+str(q['ans'])+"\n"
            profile[key]=q['ans']
        
        if key == 'user':
            user=profile[key]
            questions['remote_path']['default'] = questions['remote_path']['default'].replace('?%s?' % key ,profile[key])

    print profile

    # do string subst
    for key in profile:
        for q in profile:
            #profile[q]=profile[q].replace( '?%s?' % key, profile[key] )
            unison_prf=unison_prf.replace( '?%s?' % key, str(profile[key]) )
     
    prf_f=profile['title']
    prf=os.path.abspath( os.path.join(conf.unison_dir,prf_f+'.prf') )
    
    # create unison profile 
    f = open(prf,'w')
    f.write(unison_prf)
    f.close()
    
    # create profile
    uconf=conf.templates('unison')
    uconf['prf']=prf_f
    uconf['auto_start']=True
    conf.profiles[prf_f]=uconf
    conf.save_profiles()
    #Rainmaker.restart()


conf=RainmakerConfig()

parser = argparse.ArgumentParser(version='0.1',add_help=True)
parser.add_argument('-d','--delete', action="append", dest='del_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('--start', action="append", dest='start_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('--stop', action="append", dest='stop_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('-t','--test', action="append", dest='test_profiles', choices=conf.profiles.keys(), metavar='PROFILE',default=[])
parser.add_argument('-a','--auto', action="store_true", dest='auto_start', default=True)
parser.add_argument('-q','--quiet', action="store_true", dest='quiet',default=False)

# profile error?
perr=None

if not '-c' in sys.argv:
    parser.add_argument('-c', action="store_true",default=False,dest='create', help='[TYPE] [OPTIONS]')

else:
    idx = sys.argv.index('-c')
    
    template='unison'
    if len(sys.argv) >= idx + 2 and sys.argv[idx+1][0] != '-':
        if sys.argv[idx+1] in conf['templates']:
            template=sys.argv[idx+1]
        else:
            perr = 'Unknown profile type: %s' % sys.argv[idx+1]
        parser.add_argument('-c', action="store",dest='create',default=template, choices=conf['templates'].keys())

    else:
        parser.add_argument('-c', action="store_true",default=False,dest='create', help='[TYPE] [OPTIONS]')
    
    if not perr:
        group=parser.add_argument_group('-c [TYPE=%s] [[OPTIONS]]' % template)
        
        questions = conf['questions'][template]
        for key in questions:
            q=questions[key]
            group.add_argument('--'+key, action="store", dest='create_var_%s' %key,help=q['q'])

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
                group.add_argument('--update_var_'+key, action="store", dest=key,default='',help=str(profile_data[key]))
            elif isinstance(profile_data[key],bool):
                group.add_argument('--update_var_'+key, action="store_true", dest=key,default=profile_data[key],help=str(profile_data[key]))

    else:
        perr = 'Unknown profile'

args = parser.parse_args()

print args
if perr:
    print perr
    sys.exit()

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

if args.update_profile:
    print 'not implemented'
    sys.exit()

if len(args.del_profiles)>0:
    did_delete=False
    for arg in args.del_profiles:
        if arg in conf.profiles:

            p=conf.profiles.pop(arg)
            if p['type']=='unison':
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

if args.create:
    do_unison(conf,args)
    sys.exit()

if args.auto_start:
    for key in conf.profiles:
        if conf.profiles[key]['auto_start']==True:    
            args.start_profiles.append(key)

if not args.start_profiles:
    #start service with no active profiles
    print 'Starting with no profiles'
    sys.exit()


for i in args.start_profiles:
    print "Starting:\t%s" % i

