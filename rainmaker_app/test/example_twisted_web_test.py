from twisted.internet.defer import inlineCallbacks
from twisted.internet import defer, reactor
from twisted.web import resource
from twisted.web.server import NOT_DONE_YET

class ChildPage(resource.Resource):
    def render(self, request):
        d = defer.Deferred()
        d.addCallback(self.renderResult, request)
        reactor.callLater(1, d.callback, "hello")
        return NOT_DONE_YET

    def renderResult(self, result, request):
        request.write(result)
        request.finish()
        
class MainPage(resource.Resource):
    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild('childpage', ChildPage())


from twisted.trial import unittest
from twisted_web_test_utils import DummySite

class WebTest(unittest.TestCase):
    def setUp(self):
        self.web = DummySite(MainPage())

    @inlineCallbacks
    def test_get(self):
        response = yield self.web.get("childpage")
        self.assertEqual(response.value(), "hello")
        # if you have params / headers:
        response = yield self.web.get("childpage", {'paramone': 'value'}, {'referer': "http://somesite.com"})
