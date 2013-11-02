import re

from resources.root_resource import RootResource
from resources.files_resource import FilesResource
from resources.parts_resource import PartsResource
from resources.sync_paths_resource import SyncPathsResource
from resources.diffs_resource import DiffsResource

def resources():
    root = RootResource(
        syncs = SyncPathsResource(
            resource_id = 'sync_path_guid',
            diffs = DiffsResource(),
            files = FilesResource(
                resource_id = 'path',
                parts = PartsResource(
                    resource_id = 'phash'
                )
            )
        )
    )
    return root


    
