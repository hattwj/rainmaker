from twisted.internet import defer
from twisted.internet.task import LoopingCall

from ishell.console import Console
from ishell.command import Command

from . boot import app, stop_app
from . db.models import models_arr, SyncPath
from . lib.net.clients import ClientFactory
from . lib.net import finger_table
from . lib import util
import debug_node

console = Console(prompt="rainmaker ", prompt_delim="#")

class FilesScanCommand(Command):
    '''
        scan a sync path or all sync paths
    '''
    @defer.inlineCallbacks
    def run(self, line):
        path = ' '.join(line.split()[2:])
        if path:
            sync_paths = yield SyncPath(where=['root=?',path])
        else:
            sync_paths = yield SyncPath.all()
        if len(sync_paths)==0:
            print 'No paths found'
        for sp in sync_paths:
            sp.scan()

class DbClearCommand(Command):
    '''
        clear all records from db
    '''
    @defer.inlineCallbacks
    def run(self, line):
        for model in models_arr:
            if model.sticky_table:
                continue
            ans = yield model.deleteAll()
            print "Deleted all records in: %s\n" % model.tablename()

class DbShowCommand(Command):
    '''
        Dynamic command for showing contents of db tables
    '''
    model=None

    @defer.inlineCallbacks
    def run(self, line):
        records = yield self.model.all()
        for record in records:
            print record
        print "\n"

class DbAddSyncPathCommand(Command):
    '''
        Add a new sync path
    '''
    def run(self, line):
        password_rw = ''.join(line.split()[3:4])
        root = ' '.join(line.split()[4:])
        if password_rw == '':
            print 'empty password'
            return
        if root == '':
            print 'empty path'
            return
        d = SyncPath.new(root=root, password_rw=password_rw)
        d.addCallback(self.result)

    def result(self, result):
        print result
        
class StatFingerTableCommand(Command):
    '''
        Show contents of finger table
    '''
    def run(self, line):
        print finger_table.all_hosts()

class StatConfigCommand(Command):
    '''
        Show config
    '''
    def run(self, line):
        print 'Showing config...'
        print app

class StartUdpCommand(Command):
    '''
        Start udp multicast server
    '''
    def run(self, line):
        # start lan discovery
        app.udp_server.start()

class StartTcpCommand(Command):
    '''
        Start tcp server
    '''
    def run(self, line):
        print line
        app.tcp_server.start()

class StartDebugNodeCommand(Command):
    '''
        create rainmaker sub process to test with
    '''
    def run(self, line):
        p_tcp = app.tcp_server.listen_port
        args = '-k 512 --tcp %s' % (p_tcp+1)
        cmds=[
            'stat config',
            'start tcp',
            'net tcp ping localhost:%s' % p_tcp,
            'net tcp sync wibble localhost:%s' % p_tcp
        ]
        debug_node.create(args, cmds=cmds)

def get_addr_port(line):
    addr_port = line.split()[-1].split(':') 
    try:
        assert addr_port[0] != '', 'no address listed'
        assert len(addr_port)>1, 'no port listed'
        assert len(addr_port)==2, 'too many args'
        addr_port[1] = int(addr_port[1])
        assert addr_port[1] > 0, 'positive ports only'
        assert addr_port[1] < 2**16, 'port too high'
        addr_port = tuple(addr_port)
    except AssertionError as e:
        print "\n".join(list(e.args))
        return
    except ValueError as e:
        print "port must be number"
        return
    return addr_port

class NetPingCommand(Command):
    '''
        Check host:port for connection
    '''
    def run(self, line):
        protocol = ''.join(line.split()[2:3])
        addr_port = get_addr_port(line)
        if not addr_port:
            return
        if protocol != 'udp':
            ClientFactory.ping(addr_port)
        else:
            app.udp_server.ping(addr_port)
class NetTcpSyncCommand(Command):
    '''
        Check host:port for connection
    '''
    @defer.inlineCallbacks
    def run(self, line):
        password = ''.join(line.split()[3:4])
        if not password:
            print 'no password'
            return
        sync_path = yield SyncPath.find(where=["password_rw = ?",password], limit=1)
        if not sync_path:
            print "sync with password not found"
            return
        
        addr_port = get_addr_port(line)

        if not addr_port:
            return
        ClientFactory.sync(addr_port, app.auth, sync_path)

import sys
class ExitCommand(Command):
    '''
        Exit console
    '''
    
    def run(self, line):
        debug_node.stop_all()
        sys.stdout.flush()
        sys.exit()

# top level commands
files_command = Command('files', help='files...')
net_command = Command('net', help='networking commands')
start_command = Command('start', help='start service...')
stat_command = Command('stat', help='status commands')
db_command = Command('db', help='db commands')
exit_command = ExitCommand('exit', help='exit')
console.addChild(files_command)
console.addChild(start_command)
console.addChild(stat_command)
console.addChild(db_command)
console.addChild(net_command)
console.addChild(exit_command)

# second level commands
## net cmds
net_udp_command = Command('udp', help='udp actions')
net_tcp_command = Command('tcp', help='tcp actions')
net_command.addChild(net_udp_command)
net_command.addChild(net_tcp_command)

## start cmds
start_debug_node_command = StartDebugNodeCommand('debug_node', 'Start debug node')
start_udp_command = StartUdpCommand('udp', 'Start udp server')
start_tcp_command = StartTcpCommand('tcp', 'Start tcp server')
start_command.addChild(start_debug_node_command)
start_command.addChild(start_udp_command)
start_command.addChild(start_tcp_command)

## files cmds
files_scan_command = FilesScanCommand('scan', help='scan (path|*all)')
files_command.addChild(files_scan_command)

## stat cmds
stat_config_command = StatConfigCommand('config', help='Show config')
stat_finger_table_command = StatFingerTableCommand('fingers', help='Show contacts')
stat_command.addChild(stat_config_command)
stat_command.addChild(stat_finger_table_command)

## db cmds
db_clear_command = DbClearCommand('clear', help='clear database')
db_add_command = Command('add', help='db add commands')
db_show_command = Command('show', help='Show information about...')
db_command.addChild(db_clear_command)
db_command.addChild(db_show_command)
db_command.addChild(db_add_command)

# 3rd level
net_udp_ping_command = NetPingCommand('ping', help='ping host:port')
net_tcp_ping_command = NetPingCommand('ping', help='ping host:port')
net_tcp_sync_command = NetTcpSyncCommand('sync', help='sync host:port path')
net_udp_command.addChild(net_udp_ping_command)
net_tcp_command.addChild(net_tcp_ping_command)
net_tcp_command.addChild(net_tcp_sync_command)

db_add_sync_path_command = DbAddSyncPathCommand('sync_path', help='create sync path')
db_add_command.addChild(db_add_sync_path_command)
# add show cmd for every model
for model in models_arr:
    name = util.snake_case(model.__name__)
    cmd = DbShowCommand(name, help='show records')
    cmd.model = model
    db_show_command.addChild(cmd)

def run():
    try:
        loop_flush = LoopingCall(sys.stdout.flush)
        loop_flush.start(1)
        print 'Entering interactive mode'
        sys.stdout.flush()
        console.loop()
    except SystemExit as e:
        pass
    loop_flush.stop()
    stop_app()

    print 'Good bye'
