from watcher import *


def main():
    conf=RainmakerConfig()
    p=conf.templates['unison']
    p['local_root']='voltr555555n'
    print p.data
    conf.profiles['test' ]=p
    conf.save_profiles()

if __name__ == '__main__':
    main()
