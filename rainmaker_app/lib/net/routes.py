from resources.root_resource import RootResource
from resources.files_resource import FilesResource
#from resources.parts_resource import PartsResource
from resources.sync_paths_resource import SyncPathsResource
from resources.diffs_resource import DiffsResource

def resources():
    root = RootResource()
    root.putChild('syncs', SyncPathsResource())
    root.putChild('files', FilesResource())
    #root.putChild('parts', PartsResource())
    root.putChild('diffs', DiffsResource())
    return root


    
