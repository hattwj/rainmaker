from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer

from rainmaker_app.lib.util import Object

class BaseResource(Resource):
    def getChild(self, name, request):
        if not hasattr(request,'id'):
            request.id = name
        elif '.' in name and not hasattr(request, 'render_to'):
            request.render_to = name
        elif not hasattr(request,'sub_action'):
            request.sub_action = name
        return self
    
    def render_GET(self, request):
        # Set default responseCode
        request.setResponseCode(200)
        request.vdata = Object() # Data passed to view

        # pick action to call
        if hasattr(request, 'id') and hasattr(self, 'show'):
            request.action = 'show'
            d = self.show(request)
        elif hasattr(self, 'index'):
            request.action = 'index'
            d = self.index(request)
        else:
            request.setResponseCode(404)
            return '-Error: 404 unknown'
        
        # Finish the request
        d.addCallback( self._end, request )
        d.addErrback( self._on_error, request )
        return NOT_DONE_YET
    
    def _end(self, action, request):
        # finish render
        request.finish()

    def _on_error(self, err, request):
        print err
        request.setResponseCode(500)
        request.finish()
