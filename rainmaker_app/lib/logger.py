import logging

from rainmaker_app.conf import load
config=load('logger.yml')

init_done = False
base_style = '%(name)-12s %(levelname)-8s %(message)s' 
base_level = logging.INFO
levels = {
    'debug':logging.DEBUG,
    'info':logging.INFO,
    'warn':logging.WARN,
    'error':logging.ERROR,
    'none':logging.NOTSET
    }

# log to console
def do_init(style=None,level=None):
    global init_done
    level = levels[level] if level else levels[config['level']]
    style = style or config['style']

    if init_done == True:
        return

    init_done = True
    # set up logging to console
    logging.basicConfig(
        level=level,
        format=style
    )


def create(name='',style=None,level=None):
    do_init(level=level,style=style)
    level = levels[level] if level else levels[config['level']]
    style = style or config['style']

    log = logging.getLogger(name)
    
    if name == '':
        return log
    #handler = logging.StreamHandler()
    #handler.setLevel(level)

    # set a format which is simpler for f_log use
    #formatter = logging.Formatter(style)
    
    # tell the handler to use this format
    #handler.setFormatter(formatter) 

    #log.addHandler(handler)

    return log

# also log output to a file
def log_to_file(fpath, name ,level=None, style=None,date_style=None):
    do_init(style,level)
    level = levels[level] if level else levels[config['level']]
    date_style = date_style if date_style else config['date_style']
    style = style or config['style']
    
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

