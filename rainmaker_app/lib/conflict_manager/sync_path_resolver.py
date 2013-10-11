from . file_resolver import FileResolver
from rainmaker_app.db.models import Difference
from rainmaker_app.model.common import *

class SyncPathResolver(object):
    """ """
    transfer_agent = None

    def __init__(self, transfer_agent):
        """ """
        self.transfer_agent = transfer_agent
    
    def conflicts_resolver(self, file_resolver):
        ''' override this function to manage conflicts '''
        raise NoResolverError('No conflict resolver set')
        
    
    @classmethod
    @defer.inlineCallbacks
    def resolve_against(self, sync_paths_arr):
        """ compare sync paths and find conflicts/updates"""        
        my_files = yield Difference.between_sync_paths( *sync_paths_arr )
        resolvers = []
        while len(my_files) > 0:
            # resolve differences
            my_file = my_files.pop()
            file_resolver = FileResolver( my_file )
            file_resolver.resolve_against( my_files )
            resolvers.append( file_resolver )

            # prep for next round
            my_files = file_resolver.unrelated_files
        defer.returnValue( resolvers )
   
    def process_file_resolver(self, file_resolver):
        ''' update hosts related to resolver '''

        if file_resolver.conflict_files:
            # run conflict resolver instead
            return self.conflicts_resolver(file_resolver)        
        
        # alias for agent
        agent = self.transfer_agent
        
        t = [] # return arr of transfer objects
        
        # get resolver info
        state, sources, dests = _resolver_info(file_resolver)
        
        for sync in file_resolver.sync_paths:
            if [d for d in dests if d.sync_path_id == sync.id]:
                next # this path is already updated
            try:
                t.append( self._migrate_sync_path( sync, state, sources, dests[0]) )
            except NoActionError:
                next
        return t
            
    def _migrate_sync_path(self, sync, state, related, dest):
        ''' sync file with sync path ''' 
        agent = self.transfer_agent

        # find related files belonging to sync path
        my_file = _get_file_from(sync, related)
         
        if my_file and state == FileResolver.NEW:
            raise NoActionError('File exists')
        elif  state == FileResolver.NEW:
            # get file 
            return agent.create(sync, dest)
        
        if my_file and state == FileResolver.MOVED:
            # move file 
            return  agent.move(my_file, dest.path)
        elif state == FileResolver.MOVED:
            # get file 
            return agent.create(sync, dest)

        if my_file and state == FileResolver.MODIFIED:
            # get new or modified file for this sync
            return agent.update(sync, dest)
        
        if my_file and state == FileResolver.DELETED:
            # del file and mark as deleted
            return  agent.delete(sync, my_file)
        raise NoActionError('Nothing to do for sync path')

def _get_file_from(sync, related):
    ''' get the related file for this sync path '''
    my_file = None
    my_files = [d for d in related if d.sync_path_id == sync.id]
    if len(my_files) > 1:
        raise TooManyFilesError('Too many related files for sync path')
    elif len(my_files) == 1:
        my_file = my_files[0]
    return my_file

def _resolver_info(file_resolver):
    ''' return info about resolver '''
    dests = file_resolver.last_child.peer_files
    if not dests:
        raise NoFilesError('FileResolver has no peers.')
    sources = file_resolver.last_child.related_files
    state = file_resolver.state
    return [state, sources, dests]

class NoFilesError(Exception):
    pass
class TooManyFilesError(Exception):
    pass
class NoActionError(Exception):
    pass
class NoResolverError(Exception):
    pass
