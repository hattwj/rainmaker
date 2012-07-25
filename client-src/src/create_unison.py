import os
import sys
import copy
from watcher import *

def ask(q):
    valid=False
    while valid == False:
        print('')
        if q['default']:
            print('Default: '+str(q['default']) ) 
        q['ans']=raw_input( q['q'] ) or q['default']
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

questions = [
    {'ans':None,'default':None,'type':'str','name':'user','q':'server user name: '},
    {'ans':None,'default':'22','type':'int','name':'port','q':'server ssh port: '},
    {'ans':None,'default':'localhost','type':'str','name':'address','q':'server address: '},
    {'ans':None,'default':'~/.ssh','type':'str','name':'ssh_dir','q':'ssh dir: '},
    {'ans':None,'default':'id_rsa','type':'str','name':'ssh_key','q':'ssh private key: '},
    {'ans':None,'default':'~/sync','type':'str','name':'local_root','q':'local root: '},
    {'ans':None,'default':'/home/rainmaker/?user?','type':'str','name':'remote_root','q':'remote root: '},
    {'ans':None,'default':'10','type':'int','name':'max_backups','q':'max backups: '}
]

f=open('../conf/unison_default.prf','r')
unison_prf = f.read()
f.close()

for i,q in enumerate(questions):
    questions[i] = ask(q)
    print 'Using: '+q['ans']+"\n"
    if q['name']=='user':
        user = q['ans']
c=0
while '?' in unison_prf:
    c+=1
    for i,q in enumerate(questions):
        unison_prf=unison_prf.replace('?'+q['name']+'?',q['ans'])
    if c>3:
        break

home=os.path.expanduser('~')
c=0
fexists = True
while  fexists == True:
    prf_f = 'rainmaker-'+user+str(c or '') 
    prf=os.path.abspath( os.path.join(home,'.unison',prf_f+'.prf') )
    fexists = os.path.isfile(prf)
    c += 1
    if c > 100:
        print 'Unable to create: '+prf
        sys.exit()
f = open(prf,'w')
f.write(unison_prf)
f.close()

conf=W2UConfig('../conf/w2.yml')

uconf=conf.templates('unison')


uconf['prf']=prf_f
uconf['auto_start']=True
conf.profiles[prf_f]=uconf
conf.save_profiles()

#Rainmaker.restart()

