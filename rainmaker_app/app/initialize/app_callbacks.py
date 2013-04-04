
import yaml

class AppCallbacks(object):
    events = {}
    def __init__(self,parent,events):
        self.parent=parent
        for k in events:
            if not k in self.events:
                self.events[k] ={}
            for v in events[k]:
                self.events[k]['before_'+v]=[]
                self.events[k][v]=[]
                self.events[k]['after_'+v]=[]

    def add(self,key,val,func,**kwargs):
        self.events[key][val].append([func,kwargs])

    def run(self,name,event,**kwargs):
        for func,args in self.events[name][event]:
            func(**dict( kwargs.items()+args.items() ) )

    def trigger(self,name,event,**kwargs):
        for k in ["before_%s" % event,event,"after_%s" % event]:
            self.parent.log.debug("%s_%s" % (name,k) )
            for func,args in self.events[name][k]:
                func(**dict( kwargs.items()+args.items() ) )
