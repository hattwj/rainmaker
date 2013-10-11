def mock(objects_dict, data):
     
    klass = data['klass']
    obj = objects_dict[ klass ]()
    for k, v in data['data'].items():
        print k
        vtype = v['klass']
        vdata = v['data']
        
        if '_array' in vtype:
            val = []
            sub_vtype = vtype.replace('_array', '')

            for w in vdata:
                val.append( make_obj( *get_obj(m) ) )
        elif vtype in objects_dict.keys():
            val = objects_dict[vtype](**vdata)
        else:
            val = vdata
        setattr(obj, k, val)
    return obj

def make_obj(klass, args, kwargs, attrs, objs):
    if args and kwargs:
        obj =  objs[klass](*args,**kwargs)
    elif args:
        obj = objs[klass](*args)
    elif kwargs:
        obj = objs[klass](**kwargs)
    else:
        obj = objs[klass]
    if attrs:
        for a, data in attrs.items():
            val = mock(objs, data)
            setattr(obj, a, val) 
    return obj

def get_obj( data ):
    klass = data['klass']
    args = None
    kwargs = None
    attrs = None

    if 'args' in data.keys():
        args = data['args']
    if 'kwargs' in data.keys():
        kwargs = data['kwargs']
    if 'attrs' in data.keys():
        attrs = data['attrs']
    return [klass, args, kwargs, attrs]
