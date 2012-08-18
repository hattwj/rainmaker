from watcher import *


def main():
    conf=RainmakerConfig()
    p=conf.profiles['test']
    p.subst_all()
    print p
if __name__ == '__main__':
    main()
