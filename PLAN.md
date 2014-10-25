Most of the work left is to wire all the systems together
Top priorities:
- ability to send/recv pings
- authenticate hosts on store_host
- add hosts to dht


List of todo items:

udp_multicast:
    - periodically send out a ping on multicast
    - acts as central transport/handler for commands
    - everything sent is signed by Authorization

finger_table:
    - reserve list of hosts to use for dht
    - hosts only added when verified

dht:
    - split into buckets
    - keeps network map in memory
    - periodically send ping to all hosts

fs_events:
    - send 'recv_changes' to peers on fs event
    - inotify listen for events
    - active scan for changes

commands:
    - respond to requests

peers:
    - Active hosts that share a key with us

host:
    - has one ephemeral pubkey
    - has many sync keys

# Commands

ping:
- c: request store_host with remote details
- r: send store_host for self, if new send ping

store_host:
- c: send verifiable host details
- r: verify host details and add to dht/finger/db/peers

find_host:
- c: request host information 
- r: check dht/finger/db for host and send info via store_host

shutdown_host:
- c: notify that were shutting down
- r: remove from dht/finger/db
     forward msg to peers

send_file_part:
- c: request part of file to be sent
- r: 'recv_file_part' send requested file part to peer

recv_file_part:
- c: send file part to peer
- r: write to disc

send_file_details:
- c: request all of the file parts info for this file
- r: send file parts info for this file

recv_file_details:
- c: send file details to peer
- r: write to db

send_changes:
- c: request all changes since point x
- r: diff against x and send changes

recv_changes:
- c: notify peers that changes have occurred
- r: reply with send changes since x
