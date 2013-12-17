import rainmaker_app

def is_compatible(ver):
    ''' Is the current version of the application compatible with `ver`'''
    try:
        if rainmaker_app.version.split('.')[0:1] == ver.split('.')[0:1]:
            return True
    except:
        pass
    return False

