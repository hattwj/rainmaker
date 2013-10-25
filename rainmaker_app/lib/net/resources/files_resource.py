from base_resource import BaseResource
from rainmaker_app.db.models import MyFile
from rainmaker_app.model.common import *

class FilesResource(BaseResource):

    @defer.inlineCallbacks
    def show(self, request):
        my_file = yield MyFile.find(request.id)
        
        if my_file:
            request.write( my_file.to_json() )
        else:
            request.setResponseCode(404)
            request.write('Not Found')
