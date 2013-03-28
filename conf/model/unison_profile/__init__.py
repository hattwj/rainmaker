import os
import yaml

root = os.path.abspath(os.path.join(os.path.dirname(__file__)) )

with open( os.path.join(root,'base_command.txt'),'r') as f: 
    base_command=f.read()
with open( os.path.join(root,'attrs.yml'),'r') as f: 
    attrs=yaml.safe_load(f.read())

del(root)
