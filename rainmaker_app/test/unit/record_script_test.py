import unittest
import os

from lib import RecordScript
from lib import path

class TestRecordScript(unittest.TestCase):

    def setUp(self):
        print 'Setup'
        unittest.TestCase.setUp(self)
        self.rs = RecordScript()
        self.attrs = {
            'a': '${b}',
            'b': '${c}',
            'c': '${d}',
            'd': ' ddd ',
            'g': '${a}${b}${c}',
            'loop':"${loop} ${loop}",
            'subst_arg':'${which:${program}}',
            'program':'unison',
            'test_for_each':'${base} ${for_each:["${events_type}","path ${quote:file} "]}',
            'base':'${which:${program}}',
            'cmd_multi':'44 ${current_user} 77 ${current_user} 99',
            'nested':'${cmd_multi}',
            'events_type':'events_created',
            'events_created': "[file: \"a' aa\", file: b./bb, file: 'c:\de\eee']"
        }

    def tearDown(self):
        print 'Teardown'

    def test_subst(self):
        self.rs.attrs_update(self.attrs)
        self.assertEquals( self.rs.subst('${which:[unison]}'),path.which('unison'))
        self.assertEquals( self.rs.subst('${current_user}'),path.current_user())
        self.assertEquals( self.rs.subst('${a}',times=5), self.attrs['d'])
        self.assertEquals( self.rs.subst('${loop}',times=5), ' '.join([self.attrs['loop'] ]*2**5) )
        self.assertEquals( self.rs.subst('${subst_arg}',times=5), path.which(self.attrs['program']) )
        attrs={'events_created':self.rs.__cmd_yaml__(self.attrs,self.attrs['events_created'])}
        print self.rs.subst('${test_for_each}',attrs)
        print self.rs.subst('${nested}',attrs)
        #self.rs.attrs_subst()
        #print self.rs.attrs
