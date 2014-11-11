import logging

from rainmaker_app.lib.conf import load
config=load('logger.yml')

init_done = False 
log_level=config['level']
levels = {
    'debug':logging.DEBUG,
    'info':logging.INFO,
    'warn':logging.WARN,
    'error':logging.ERROR,
    'none':logging.NOTSET
    }

verbosity=0

def set_verbosity(val):
    ''' Set logging verbosity '''
    global verbosity
    global config

    if val <=0:
        val = 0
    elif val >= len(config['styles']):
        val = len(config['styles'])-1
    verbosity = val

def create(name='',style=None,level=None):
    global log_level
    global config
    global verbosity
    cur_v = config['verbosity'][name]
    if verbosity < cur_v:
        level = 'error'
    else:
        level = log_level
    #level = 'info'
    level = levels[level] if level else levels[log_level]
    style = style if style else config['styles'][verbosity]

    log = logging.getLogger(name)
    log.v=verbosity

    if log.handlers:
        handler = log.handlers[0] 
    else:
        handler = logging.StreamHandler()
        log.addHandler(handler)

    handler.setLevel(level)
    log.setLevel(level)

    # set a format which is simpler for f_log use
    formatter = logging.Formatter(style)
    
    # tell the handler to use this format
    handler.setFormatter(formatter) 

    return log

# also log output to a file
def log_to_file(fpath, name ,level=None, style=None,date_style=None):
    level = levels[level] if level else levels[log_level]
    date_style = date_style if date_style else config['date_style']
    style = style if style else config['log_file_style']
    
    log = logging.getLogger(name)

    # define a Handler
    handler = logging.FileHandler(fpath)
    handler.setLevel( level )
    
    # set a format which is simpler for handler use
    formatter = logging.Formatter(style,date_style)
    
    # tell the handler to use this format
    handler.setFormatter(formatter)
    
    # add the handler to the logger
    log.addHandler(handler)
    
    return log

