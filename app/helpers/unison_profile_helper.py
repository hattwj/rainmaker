
def cmd_base(profile):
     return '''unison \
    /home/ubuntu/rainmaker/client/tmp/sync1 \
    ssh://ubuntu@localhost:22//home/ubuntu/rainmaker/client/tmp/sync2 \
    -ui text \
    -auto \
    -batch \
    -sshargs "-i /home/ubuntu/.ssh/rain" \
    -ignore 'Name .DS_Store' \
    -ignore 'Name Thumbs.db' \
    -ignore 'Name .*' \
    -ignore 'Name temp.*' \
    -ignore 'Name *~' \
    -ignore 'Name .*~' \
    -ignore 'Name *.o' \
    -ignore 'Name *.tmp' \
    -ignore 'Name lost+found' \
    -ignore 'Name LOST.DIR' \
    -ignore 'Name temp_*' \
    -backuplocation 'central' \
    -backup 'Name *' \
    -backupprefix '$VERSION.' \
    -backupdir 'ssh://ubuntu@localhost:22//home/ubuntu/rainmaker/client/tmp/backups' \
    -maxbackups  10 \
    -confirmbigdel=false
'''
