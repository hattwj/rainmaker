from twisted.internet import protocol, reactor, defer

class RainPP(protocol.ProcessProtocol):
    def __init__(self):
        self.data = ""
    def exit(self):
        self.transport.write("exit\r")
        self.transport.loseConnection()
    def connectionMade(self):
        print "connectionMade!"
    def send(self, cmd):
        print 'sending: '+ cmd
        self.transport.write(cmd+"\n\r")
    def outReceived(self, data):
        print "outReceived! with %d bytes!" % len(data)
        print data
        self.data = self.data + data
    def errReceived(self, data):
        print "errReceived! with %d bytes!" % len(data)
        print data
        self.data = self.data + data
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

procs = {}

def get(name, args=None):
    '''
        return or create and return a rainmaker subprocess
    '''
    global procs
    if isinstance(args, str):
        args = args.split()
    if not isinstance(args, list): 
        args=[]
    if name in procs:
        return procs[name]
    args = ["./rainmaker.py", '-i'] + args
    pp = RainPP()
    procs[name] = pp
    reactor.spawnProcess(pp, args[0], args, {})
    return pp

def stop_all():
    global procs
    for k, pp in procs.iteritems():
        print 'Signaling sub process to close'
        pp.exit()

