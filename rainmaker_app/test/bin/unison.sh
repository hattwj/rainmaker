#!/usr/bin/env bash
unison \
    /home/ubuntu/rainmaker/client/tmp/sync1 \
    ssh://ubuntu@localhost:22//home/ubuntu/rainmaker/client/tmp/sync2 \
    -ui text \
    -auto \
    -batch \
    -sshargs "-i /home/ubuntu/.ssh/rain" \
    -ignore 'Name .DS_Store' \
    -ignore 'Name Thumbs.db' \
    -ignore 'Name temp.*' \
    -ignore 'Name *~' \
    -ignore 'Name .*~' \
    -ignore 'Name *.o' \
    -ignore 'Name *.tmp' \
    -ignore 'Name lost+found' \
    -ignore 'Name LOST.DIR' \
    -backuplocation 'central' \
    -backup 'Name *' \
    -backupprefix '$VERSION.' \
    -backupdir 'ssh://ubuntu@localhost:22//home/ubuntu/rainmaker/client/tmp/backups' \
    -maxbackups  10 \
    -confirmbigdel=false
