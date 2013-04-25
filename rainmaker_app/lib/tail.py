
class Tail(object):
    "monitor a file for new lines"
    def __init__(self,fin):
        self.fin = fin
        self.running = False
        self.where = None


    def readlines_then_tail(self):
        "Iterate through lines and then tail for further lines."
        self.running = True
        while self.running==True:
            line = self.fin.readline()
            if line:
                line = self.filter(line)
                if line:
                    yield line
            else:
                self.tail()
     
    def tail(self,break_on_empty=False):
        "Listen for new lines added to file."
        while self.running==True:
            self.where = self.fin.tell()
            line = self.fin.readline()
            if not line:
                self.fin.seek(self.where)
                if break_on_empty:
                    break
            line = self.filter(line)
            if line:
                yield line

    def filter(self,line):
        "replace this function to provide custom formatting"
        "returning False prevents the line from yielding"
        return line.rstrip('\n')

    def reseek(self):
        ''' seek to last position if overwritten'''
        if not self.where:
            return
        self.fin.seek(self.where)

    def new_lines(self):
        "yield newlines and return"
        self.running = True
        for line in self.tail(break_on_empty=True):
            yield line
