import unittest
from os import remove

from rainmaker_app.lib import path
from rainmaker_app.lib.tail import Tail

class TestTail(unittest.TestCase):

    def setUp(self):
        print 'Setup'
        unittest.TestCase.setUp(self)
        self.temp_file = path.rel('tmp','test_tail.swp')
        self.temp = open(self.temp_file,'w')
        self.temp.write(self.create_lines(1,3))
        self.temp.flush()
        self.f = open(self.temp_file,'r')
        self.tail = Tail(self.f)
    
    def tearDown(self):
        print '''Teardown'''
        self.f.close()
        self.temp.close()
        remove(self.temp_file)

    def test_new_lines(self):
        ''' check file for new lines'''
        self.temp.write(self.create_lines(4,6))
        self.temp.flush()
        self.expect_lines(self.create_lines(1,6))
    
    def test_overwrite(self):
        ''' test tail behavior during file overwrite '''
        self.expect_lines(self.create_lines(1,3))
        temp = open(self.temp_file,'w')
        temp.write(self.create_lines(1,20,'eee'))
        temp.flush()
        self.tail.reseek()
        self.expect_lines(self.create_lines(4,20,'eee'))
        temp.close()
    
    def test_filter(self):
        def filter(line):
            print line
        
        self.tail.filter = filter
        for line in self.tail.new_lines():
            pass

    def expect_lines(self,lines_str):
        ''' assert expected output from tail '''
        lines = lines_str.split("\n")
        counter = 0
        for line in self.tail.new_lines():
            self.assertEquals(line,lines[counter])
            counter += 1
        self.assertEquals(counter+1,len(lines))
        

    def create_lines(self,start,n,suffix='aaa'):
        ''' create new lines helper '''
        result=''
        for i in range(start,n+1):
            result += "%s %s\n" % (suffix, str(i)*10)
        return result
