from . common import *

class Difference(DBObject):

    @classmethod
    def compare(klass, id1, id2):
        return  klass.find( where=["sync_path_id = ? or sync_path_id = ?", id1, id2]) 
   
    @classmethod
    @defer.inlineCallbacks
    def resolve(klass, id1, id2):
        """ resolve differences between two sync_paths """
        # find differences
        diffs = yield klass.compare(id1, id2)
        where_ids = [my_file.id for my_file in diffs]
        my_files = yield MyFile.find_many(where_ids) 
        defer.returnValue( my_files )

