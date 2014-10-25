from twisted.internet import defer
from ishell.console import Console
from ishell.command import Command

from . boot import app, stop_app
from . db.models import *
from . lib.net.clients import ClientFactory
from . lib.net import finger_table

console = Console(prompt="rainmaker ", prompt_delim="#")

class ConfigCommand(Command):
    def run(self, line):
        print 'Showing config...'
        print app

class HostsCommand(Command):
    @defer.inlineCallbacks
    def run(self, line):
        print "Showing all Hosts..."
        hosts = yield Host.all()
        print hosts
        print ''

class AuthsCommand(Command):
    @defer.inlineCallbacks
    def run(self, line):
        print "Showing all auths..."
        auths = yield Authorization.all()
        print auths
        print ''

class FingerTableCommand(Command):
    def run(self, line):
        print finger_table.all_hosts()

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

show_command = Command('show', help='Show information about...')
config_command = ConfigCommand('config', help='Show config')
auths_command = AuthsCommand("auths", help="Show all auths")
hosts_command = HostsCommand("hosts", help="Show all hosts")
finger_table_command = FingerTableCommand('fingers', help='Show contacts')

start_command = Command('start', help='start service...')
start_udp_command = StartUdpCommand('udp', 'Start udp server')
start_tcp_command = StartTcpCommand('tcp', 'Start tcp server')

ping_command = PingCommand('ping', help='ping host:port udp|*tcp')
exit_command = ExitCommand('exit', help='exit')

def run():
    console.addChild(show_command)
    show_command.addChild(auths_command)
    show_command.addChild(config_command)
    show_command.addChild(hosts_command)
    show_command.addChild(finger_table_command)
    console.addChild(start_command)
    start_command.addChild(start_udp_command)
    start_command.addChild(start_tcp_command)
    console.addChild(ping_command)
    console.addChild(exit_command)
    try:
        console.loop()
    except SystemExit as e:
        print 'Good bye'
