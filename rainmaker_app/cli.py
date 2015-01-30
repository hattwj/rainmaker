import argparse


def parse(app, version, args=None):
    ''' 
        command line parser
    '''
    from rainmaker_app.lib import logger
    parser = argparse.ArgumentParser(version=version, add_help=True)
    parser.add_argument('-i', action="store_true", dest='start_console', default=False)
    # set config  path
    parser.add_argument('-c', '--config', action="store", dest='config_path')
    # set user dir
    parser.add_argument('--dir', action="store", dest='user_dir')
    # don't log to screen
    parser.add_argument('-q','--quiet', action="store_true", dest='log.quiet')
    # set logfile path
    parser.add_argument('--log', 
        action="store", 
        dest='log.level', 
        choices=logger.levels.keys())
    # Dont broadcast
    parser.add_argument('--nobroadcast', 
        action="store_false", 
        dest='udp_server_options.broadcast')
    # Do broadcast
    parser.add_argument('--broadcast', 
        action="store_true",
        dest='udp_server_options.broadcast')
    # ephemeral key size
    parser.add_argument('-k', action="store", 
        dest='auth_options.key_size')
    # udp: listen_port, broadcast, multicast
    parser.add_argument('--udp-b', action="store", 
        dest='udp_server_options.broadcast_port')
    parser.add_argument('--udp', action="store", 
        dest='udp_server_options.listen_port')
    parser.add_argument('-m','--mgroup', action="store", 
        dest='udp_server_options.multicast_group')
    parser.add_argument('--tcp', action="store", 
        dest='tcp_server_options.listen_port')
    # debug script
    parser.add_argument('--script', action="store", 
        dest='debug_script_path')
    
    keys = ['udp_server_options.broadcast_port',
        'udp_server_options.listen_port',
        'tcp_server_options.listen_port',
        'auth_options.key_size']
    result = {}
    # parse args and convert result to dict
    kargs = vars( parser.parse_args(args))
    # load script if specified
    for k, v in kargs.iteritems():
        if v:
            if k in keys:
                result[k] = int(v)
            else:
                result[k] = v

    return result

