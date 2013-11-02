from base_resource import BaseResource
from rainmaker_app.db.models import MyFile
from rainmaker_app.model.common import *

class PartsResource(BaseResource):

    @defer.inlineCallbacks
    def delete(self, request):
        my_file = yield MyFile.find(request.id)
        
        if my_file:
            result = yield my_file.delete_file()
            request.write( result )
        else:
            request.setResponseCode(404)
            request.write('Not Found')
    
    @defer.inlineCallbacks
    def show(self, request):
        my_file = yield MyFile.find(request.id)
        
        if my_file:
            request.write( my_file.to_json() )
        else:
            request.setResponseCode(404)
            request.write('Not Found')

