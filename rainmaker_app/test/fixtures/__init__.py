import os
import yaml

root = os.path.abspath(os.path.join(os.path.dirname(__file__)) )

with open( os.path.join(root,'attrs_bag_data.yml'),'r') as f: 
    attrs_bag_data=yaml.safe_load(f.read())

del(root)

