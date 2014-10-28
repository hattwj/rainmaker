from twisted.internet import defer
from ishell.console import Console
from ishell.command import Command

from . boot import app, stop_app
from . db.models import models_arr, SyncPath
from . lib.net.clients import ClientFactory
from . lib.net import finger_table
from . lib import util

console = Console(prompt="rainmaker ", prompt_delim="#")

class FilesScanCommand(Command):
    def run(self, line):
        path = ' '.join(line.split()[2:])
        if path:
            sync_paths = SyncPath(where=['root=?',path])
        else:
            sync_paths = SyncPath.all()
        if len(sync_paths)==0:
            print 'No paths found'
        for sp in sync_paths:
            sp.scan()

class DbClearCommand(Command):
    
    @defer.inlineCallbacks
    def run(self, line):
        for model in models_arr:
            if model.sticky_table:
                continue
            ans = yield model.deleteAll()
            print "Deleted all records in: %s\n" % model.tablename()

class DbShowCommand(Command):
    model=None

    @defer.inlineCallbacks
    def run(self, line):
        records = yield self.model.all()
        for record in records:
            print record
        print ''

class DbAddSyncPathCommand(Command):
    def run(self, line):
        path = ' '.join(line.split()[3:])
        if path != '':
            sync_path = SyncPath(root=path)
            sync_path.save().addCallback(self.scan)
        else:
            print 'empty path'

    def scan(self, sync_path):
        sync_path.scan()
        
class StatFingerTableCommand(Command):
    def run(self, line):
        print finger_table.all_hosts()

class StatConfigCommand(Command):
    def run(self, line):
        print 'Showing config...'
        print app

class StartUdpCommand(Command):
    def run(self, line):
        # start lan discovery
        app.udp_server.start()

class StartTcpCommand(Command):
    def run(self, line):
        print line
        app.tcp_server.start()

class PingCommand(Command):
    def run(self, line):
        protocol = ''.join(line.split()[2:3])
        addr_port = ''.join(line.split()[1:2]).split(':')
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
        if protocol != 'udp':
            ClientFactory.ping(addr_port)
        else:
            app.udp_server.ping(addr_port)

import sys
class ExitCommand(Command):
    def run(self, line):
        stop_app()
        sys.exit()

# top level commands
files_command = Command('files', help='files...')
start_command = Command('start', help='start service...')
stat_command = Command('stat', help='status commands')
db_command = Command('db', help='db commands')
ping_command = PingCommand('ping', help='ping host:port udp|*tcp')
exit_command = ExitCommand('exit', help='exit')
console.addChild(files_command)
console.addChild(start_command)
console.addChild(stat_command)
console.addChild(db_command)
console.addChild(ping_command)
console.addChild(exit_command)

# second level commands
start_udp_command = StartUdpCommand('udp', 'Start udp server')
start_tcp_command = StartTcpCommand('tcp', 'Start tcp server')
start_command.addChild(start_udp_command)
start_command.addChild(start_tcp_command)

files_scan_command = FilesScanCommand('scan', help='scan (path|*all)')
files_command.addChild(files_scan_command)

stat_config_command = StatConfigCommand('config', help='Show config')
stat_finger_table_command = StatFingerTableCommand('fingers', help='Show contacts')
stat_command.addChild(stat_config_command)
stat_command.addChild(stat_finger_table_command)

db_clear_command = DbClearCommand('clear', help='clear database')
db_add_command = Command('add', help='db add commands')
db_show_command = Command('show', help='Show information about...')
db_command.addChild(db_clear_command)
db_command.addChild(db_show_command)
db_command.addChild(db_add_command)

# 3rd level
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
        console.loop()
    except SystemExit as e:
        pass
    print 'Good bye'
