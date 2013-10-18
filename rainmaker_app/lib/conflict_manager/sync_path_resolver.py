from . file_resolver import FileResolver
from rainmaker_app.model.common import *

class SyncPathResolver(object):
    """ """
    transfer_agent = None

    def __init__(self, transfer_agent):
        """ """
        self.transfer_agent = transfer_agent
    
    def conflicts_resolver(self, file_resolver):
        ''' override this function to manage conflicts '''
        raise NoConflictsResolverError('No conflict resolver set')
           
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
                t.append( self._migrate_sync_path( sync, state, sources, dests) )
            except NoActionError:
                next
        return t
            
    def _migrate_sync_path(self, sync, state, related, peers):
        ''' sync file with sync path ''' 
        agent = self.transfer_agent

        # find related files belonging to sync path
        old_file = _get_file_from(sync, related)
        new_file = _get_file_from(sync, peers)
        dest = peers[0]

        if new_file:
            raise NoActionError('Already changed')

        if old_file == None or state == FileResolver.NEW:
            # get file
            return agent.create(sync, dest)
        
        if state == FileResolver.MODIFIED:
            # get new or modified file for this sync
            return agent.update(sync, dest)
        
        if state == FileResolver.MOVED:
            # move file 
            return  agent.move(old_file, dest.path)
 
        if state == FileResolver.DELETED:
            # del file and mark as deleted
            return  agent.delete(sync, old_file)
        raise UnknownActionError('Nothing to do for sync path')

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
    peers = file_resolver.last_child.peer_files
    if not peers:
        raise NoFilesError('FileResolver has no peers.')
    related = file_resolver.last_child.related_files
    state = file_resolver.state
    return [state, related, peers]

class NoFilesError(Exception):
    pass
class TooManyFilesError(Exception):
    pass
class NoActionError(Exception):
    pass
class UnknownActionError(Exception):
    pass
class NoConflictsResolverError(Exception):
    pass
