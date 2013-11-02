class Object:
    ''' Anonymous Object class'''
    pass

import json
class ExportArray(list):
    def to_json(self):
        result = []
        for v in self:
            if hasattr(v, 'serialized_data'):
                result.append(v.serialized_data)
            else:
                result.append(v)
        return json.dumps(result)
