class Callbacks(object):
    def __init__(self,parent,events):
        self.events = {}
        self.parent=parent
        for event in events:
            self.add(event)

    def add(self,event,single=False):
        events = ["before_%s" % event,event,"after_%s" % event]            
        if single:
            events = [event]
        for v in events:
            if not v in self.events:
                self.events[v] =[]
            else:
                pass

    def register(self,key,func,**kwargs):
        self.events[key].append([func,kwargs])

    def run(self,event,**kwargs):
        for func,args in self.events[event]:
            func(**dict( kwargs.items()+args.items() ) )

    def trigger(self,event,**kwargs):
        result = True
        for k in ["before_%s" % event,event,"after_%s" % event]:
            self.parent.log.debug("event %s" % k )
            for func,args in self.events[k]:
                f_result = func(**dict( kwargs.items()+args.items()+{'this':self.parent}.items() ) )
                if f_result == False:
                    self.parent.log.debug("event series aborted in: %s" % k)
                    result = False
            if result == False:
                break
        return result
