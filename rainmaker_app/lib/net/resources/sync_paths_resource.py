from base_resource import BaseResource
from rainmaker_app.db.models import SyncPath
from rainmaker_app.model.common import *
from rainmaker_app.lib.util import ExportArray

class SyncPathsResource(BaseResource):
    
    @defer.inlineCallbacks
    def index(self, request):
        ''' list all '''
        sync_paths = yield SyncPath.all() 
        sync_paths = ExportArray(sync_paths)
        request.write( sync_paths.to_json() )

    @defer.inlineCallbacks
    def update(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
            request.args['sync_path_guid']], limit = 1)
        if not sync_path:
            request.setResponseCode(404)
            request.write('sync path not Found')
            return
        
        sync_path.safe_update( request.args['sync_path'] )

        yield sync_path.save()
        if sync_path.errors:
            errors = ExportArray( sync_path.errors )
            request.write( errors.to_json() )
        else:
            request.write( sync_path.to_json() )

    @defer.inlineCallbacks
    def show(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
            request.args['sync_path_guid']], limit = 1)
        if not sync_path:
            request.setResponseCode(404)
            request.write('sync path not Found')
            return
                
        request.write( sync_path.to_json() )
