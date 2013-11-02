from base_resource import BaseResource
from rainmaker_app.db.models import MyFile, SyncPath
from rainmaker_app.model.common import *
from rainmaker_app.lib.util import ExportArray

#from sync_path_resource import authenticate

class FilesResource(BaseResource):
    
    @defer.inlineCallbacks
    def update(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
                request.args['sync_path_guid']
            ], limit = 1)
        print request.args
        # Automatically version files?
        # Allow bulk update instead
        # Both. This function should allow appending
        
        my_file = yield MyFile.find(where=[
            'sync_path_id = ? AND path = ? AND next_id IS NULL',
            sync_path.id,
            request.args['path']
        ], limit = 1)
        
        if not my_file:
            request.setResponseCode(404)
            request.write('File path not found')
            return

        my_file.updateAttrs( request.args['file'] )
        yield my_file.save()
        if my_file.errors:
            request.setResponseCode(400)
            request.write( my_file.errors )
            return
        request.write( my_file.to_json() )
    
    # This method should allow wipe replace if requested
    # Cascade delete all associated data and replace
    @defer.inlineCallbacks
    def create(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
                request.args['sync_path_guid']
            ], limit = 1)
        
        my_file = MyFile.safe_init(**request.args['file'])
        my_file.sync_path_id = sync_path.id
        yield my_file.save()
        
        if not my_file.errors:
            request.write( my_file.to_json() )
        else:
            request.setResponseCode(400)
            request.write(str(my_file.errors))
   
    # TODO: add delete many support
    @defer.inlineCallbacks
    def delete(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
            request.args['sync_path_guid']], limit = 1)
        my_file = yield MyFile.find(where=[
            'sync_path_id = ? AND path = ?', 
            sync_path.id, request.args['path'] ])
        
        if my_file:
            result = yield my_file.delete()
            request.write( result )
        else:
            request.setResponseCode(404)
            request.write('Not Found')
    
    @defer.inlineCallbacks
    def show(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
            request.args['sync_path_guid']], limit = 1)
        if not sync_path:
            request.setResponseCode(404)
            request.write('sync path not Found')
            return

        my_file = yield MyFile.find( where = [
            'sync_path_id = ? AND path = ? AND next_id IS NULL',
            sync_path.id, request.args['path'] ], limit = 1)
        
        if my_file:
            request.write( my_file.to_json() )
        else:
            request.setResponseCode(404)
            request.write('Not Found')
    
    @defer.inlineCallbacks
    def index(self, request):
        sync_path = yield SyncPath.find( where = ['guid = ?', 
            request.args['sync_path_guid'] ], limit = 1)
        if not sync_path:
            request.setResponseCode(404)
            request.write('sync path not Found')
            return
        my_files = yield sync_path.my_files.get(where=['next_id IS NULL'])
        
        if my_files:
            my_files = ExportArray( my_files )
            request.write( my_files.to_json() )
        else:
            request.setResponseCode(404)
            request.write('Not Found')
  
