import logging

init_done = False
base_style = '%(name)-12s %(levelname)-8s %(message)s' 
base_level = logging.INFO
levels = ['debug','info','warn','error']
# log to console
def do_init(style=None, level=None,name=''):
    global init_done
    global base_style
    global base_level
    
    level = level or base_level
    style = style or base_style

    if init_done == True:
        return
    init_done = True
    # set up logging to console
    logging.basicConfig(
        level=level,
        format=style
    )


def create(name='',level=None,style=None):
    do_init()
    global base_style
    global base_level
    
    level = level or base_level
    style = style or base_style
    
    do_init(level=level,style=style)

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
def send_log_to_file(fpath, log,level=None, style=None):
    do_init()
    global base_style
    global base_level
    
    level = level or base_level
    style = style or base_style

    # define a Handler
    handler = logging.FileHandler(fpath)
    handler.setLevel( level )
    
    # set a format which is simpler for handler use
    formatter = logging.Formatter(style)
    
    # tell the handler to use this format
    handler.setFormatter(formatter)
    
    # add the handler to the logger
    log.addHandler(handler)
    
    return True

