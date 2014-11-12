import os
import yaml

import rainmaker_app

def load(path,abspath=False,from_dir=None):
    ''' load yml file from conf directory '''
    global root

    from_dir = from_dir if from_dir else root
    if not abspath: 
        path = ('%s/%s' % (from_dir,path)).split('/') 
        path = os.path.sep.join(path)
    with open(path, 'r') as f: 
        data=yaml.safe_load(f.read())
    return data

def t(path,attrs={},paths=[]):
    ''' run translation '''
    global locale_script
    
    if not locale_script:
        set_locale(locale)
    return locale_script.subst('${%s}' % path,attrs,search_paths=paths )

def set_locale(val):
    global locale
    global locale_dict
    global locale_script

    locale = val
    locale_dict = load('locale/%s.yml' % locale)[locale]

    # late import of RecordScript to prevent circular depends
    from .record_script import RecordScript
    locale_script = RecordScript(locale_dict)
 
root = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        'conf'
    )
)

locale='en'
locale_dict = None
locale_script = None
