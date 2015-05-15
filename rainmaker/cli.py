import argparse

from rainmaker import logger
from rainmaker.main import Application

def parse(args=None):
    ''' 
        command line parser
    '''
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--version', action='version', version=Application.version)
    #parser.add_argument('-i', action="store_true", dest='start_console', default=False)
    # set config  path
    parser.add_argument('-c', '--config', action="store", dest='config_path')
    # set user dir
    parser.add_argument('--dir', action="store", dest='user_dir')
    ## don't log to screen
    #parser.add_argument('-q','--quiet', action="store_true", dest='log.quiet')
    ## set logfile path
    #parser.add_argument('--log', 
    #    action="store", 
    #    dest='log.level', 
    #    choices=logger.levels.keys())
    result = {}
    # parse args and convert result to dict
    kargs = vars( parser.parse_args(args))
    kargs = {k:v for k, v in kargs.items() if v is not None}
    return kargs
