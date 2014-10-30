from twisted.internet import protocol, reactor, defer

class RainPP(protocol.ProcessProtocol):
    def __init__(self, cmds):
        if not isinstance(cmds, list):
            cmds = []
        self.cmds = cmds
        self.data = ""
    def exit(self):
        self.transport.write("exit\r")
        self.transport.loseConnection()
    def connectionMade(self):
        print "connectionMade!"
        for cmd in self.cmds:
            print 'sending: '+ cmd
            self.transport.write(cmd+"\r")
    def outReceived(self, data):
        print "outReceived! with %d bytes!" % len(data)
        print data
        self.data = self.data + data
    def errReceived(self, data):
        print "errReceived! with %d bytes!" % len(data)
    def inConnectionLost(self):
        print "inConnectionLost! stdin is closed! (we probably did it)"
    def outConnectionLost(self):
        print "outConnectionLost! The child closed their stdout!"
        # now is the time to examine what they wrote
        print "debug node:", self.data
    def errConnectionLost(self):
        print "errConnectionLost! The child closed their stderr."
    #def processExited(self, reason):
    #    print "processExited, status %d" % (reason.value.exitCode,)
    #def processEnded(self, reason):
    #    print "processEnded, status %d" % (reason.value.exitCode,)

procs = []
def create(args=None, cmds=None):
    global procs
    if isinstance(args, str):
        args = args.split()
    if not isinstance(args, list): 
        args=[]
    args = ["./rainmaker.py", '-i'] + args 
    pp = RainPP(cmds)
    procs.append(pp)
    reactor.spawnProcess(pp, args[0], args, {})
    return pp

def stop_all():
    global procs
    for pp in procs:
        print 'Signaling sub process to close'
        pp.exit()

