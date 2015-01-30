Top priorities:
- ability to send/recv pings
- authenticate hosts on store_host

List of todo items:

tcp_server:
    - authenticate connections
    - provide sync interface
        - send/recv files

sync_path_manager:
    - map fs_man events 
        - tox_manager
        - scanner
    - params: sync_path
    - methods:
        - scan
        - shutdown
    - errors:
        - scan aborted
        - path missing

    scanner:
        - params: sync_path
        - errors:
            - path missing
        - events:
            - scan_complete
            - scan_aborted
            - scan_started
        - methods:
            - start/abort
            - rescan path
    
    tox_manager:
        - listen for peers
        - listen for fs events
        - broadcast peers
        - broadcast fs event
        - params: sync_path
        - errors:
            - NotConnected
            - NoPeers
        - methods: 
            - l send_fs_event
            - l send_peer_info
            - delegate_authority
        - event handlers:
            - r store_fs_event peer_id, event_params
            - r store_peer_info
            - r recv_authority become primary
        - events:
            - r new_fs_event peer, event
            - r new_peer peer
        - classes:
            fs_event
            peer_event

    sync_manager:
        - listen for tox peer events
        - listen for tox fs events
        - listen for udp peer events
        - methods:
            - add_peer
            - fs_event
        - generate connection for new peers
        - timer to regulate
            - old/invalid peers
            - connection attempts
        - manage connections
        - params: none

        sync_client:
            - authenticate peer
            - complete sync and disconnect
            - gather remote fs state
            - send fs states
            - get/send fs parts
            - calc fs differences
            - get/send file_parts
            - params: sync_path, peer
            - methods:
                - connect
                - disconnect
            - errors:
                - connection lost
            - events:
                sync_complete

            session:
                - hold connection session info
                - params: client/server connection
            
            client_authenticator:
                - authenticate session
                - params: client_connection
                - events:
                    auth_complete
                - errors:
                    auth_failed
            
            client_file_state_sync:
                - sync fs states
                - log new_files, conflicts
                - params: client_connection

            client_file_part_sync:
                - get missing file parts data
                - params: client_connection


    fs_manager:
        - update db on fs changes
        - params: sync_path
        - methods:
            - start / stop
            - ignore_file
        - events:
            - file_change_event event
        - classes:
            - ignored_file
            - file_event

udp_multicast:
    - periodically send out a ping on multicast
    - acts as central transport/handler for commands
    - everything sent is signed by Authorization

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
