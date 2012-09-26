import rain_forced
import sys
import re
import datetime

user='ubuntu'
mode='unison'
sys.argv.append(user)
sys.argv.append(mode)

rain_forced.init()

conn=rain_forced.SSHConnInfo.current()
f = open( conn.user.log_path )
t=rain_forced.Tail(f)



# get filter
t.filter=rain_forced.Tail.get_log_filter()

for line in t.new_lines():
    print line

print 'done'
