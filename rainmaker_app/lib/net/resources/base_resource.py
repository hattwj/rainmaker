from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer

from rainmaker_app.lib.util import ExportArray, Object

def _end( action, request):
    ''' actions running at end of render '''
    # finish render
    request.finish()

def _on_error( err, request):
    ''' an error occurred during the render '''
    print err
    request.setResponseCode(500)
    request.finish()
    raise err#Exception('Resource handler error')

def strip_arg_arrays(args):
    ''' strip arrays out of request.args '''
    for k, v in args.iteritems():
        if hasattr(v,'keys'):
            # test for dicts
            args[k] = strip_arg_arrays(v) 
        elif not hasattr(v, 'splitlines'):
            # not a string (its an array/list)
            if len(v) == 1:
                # convert to string
                args[k] = v[0]
        

def render_wrapper(func):    
    ''' render decorator '''
    def sub_render_wrapper(self, request):
        ''' nested func to access func parameters'''
        # set response code
        request.setResponseCode(200)
        strip_arg_arrays(request.args)

        # run resource
        d = func(self, request) # defer or string
        if not hasattr(d, 'addCallback'):
            return d # string
        
        # Finish the request
        d.addCallback( _end, request )
        d.addErrback( _on_error, request )
        return NOT_DONE_YET
    return sub_render_wrapper

class BaseResource(Resource):
    cur_cert = None
    resource_id = None
    
    def __init__(self,**kwargs):
        Resource.__init__(self)
        self.regxs = {}
        for k, v in kwargs.iteritems():
            if k == 'resource_id':
                self.resource_id = v
            else:
                self.putChild(k,v)

    def getChild(self, name, request):
        #print 'class: %s name: %s' % (self.__class__.__name__, name) 
        if self.resource_id:
            request.args[self.resource_id] =  name
        # use current resource
        return self
 
    @render_wrapper
    def render_DELETE(self, request): 
        if hasattr(self,'delete'):
            return self.delete(request)
        
        request.setResponseCode(404)
        return 'Error: 404 unknown action DELETE'
    
    @render_wrapper
    def render_PUT(self, request):
        # pick action to call
        if hasattr(self, 'update'):
            return self.update(request)
        
        request.setResponseCode(404)
        return '-Error: 404 unknown action update'
    
    @render_wrapper
    def render_POST(self, request):

        # pick action to call
        if hasattr(self, 'create'):
            return self.create(request)
        
        request.setResponseCode(404)
        return '-Error: 404 unknown action create'
         
    @render_wrapper 
    def render_GET(self, request):
        # pick action to call
        if self.resource_id in request.args.keys()\
            and hasattr(self, 'show'):
            return self.show(request)
        
        if hasattr(self, 'index'):
            return self.index(request)
        
        request.setResponseCode(500)
        return "%s-Error: 500 unknown" % self.__class__.__name__
         
