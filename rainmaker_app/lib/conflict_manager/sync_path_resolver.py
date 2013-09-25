
from . file_resolver import FileResolver
from rainmaker_app.db.models import Difference
from rainmaker_app.model.common import *

class SyncPathResolver(object):
    
    @defer.inlineCallbacks
    def __init__(self, sync_paths_arr):
        """ """
        my_files = yield Difference.between_sync_paths( *sync_paths_arr )
        differences = []
        while len(my_files) > 0:
            my_file = my_files.pop()
            file_resolver = FileResolver(my_file)
            file_resolver.resolve_against( my_files )
            self.assertEquals( file_resolver.state, expected_state ) 
            differences.append(file_resolver)
            # prep for next round
            my_files = file_resolver.unrelated_files
        defer.returnValue( differences )
        
end
