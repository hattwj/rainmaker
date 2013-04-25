import os
import yaml
import profile

root = os.path.abspath(os.path.join(os.path.dirname(__file__)) )

def load(path,abspath=False,from_dir=None):
    from_dir = from_dir if from_dir else root
    if not abspath: 
        path = ('%s/%s' % (from_dir,path)).split('/') 
        path = os.path.sep.join(path)
    with open( path,'r') as f: 
        data=yaml.safe_load(f.read())
    return data

