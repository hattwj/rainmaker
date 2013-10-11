@defer.inlineCallbacks 
def defer_conflicts(self, file_resolver):
    ''' defer conflicts - add them to conflicts table  '''
    result = []
    conflicts = file_resolver.conflict_files
    if not conflicts:
        defer.returnValue(result)
    
    my_file = file_resolver.my_file
    for conflict in conflicts:
        result.append(
            yield Conflict(my_file_id1=my_file.id, my_file_id2=conflict.id).save()
        )
    defer.returnValue( result )

