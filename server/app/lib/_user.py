import os

class User(object):
    base_path = None

    def __init__(self):
        self.name = None
        self.log_file = None
        self.sync_path = None
        self.last_login = None
    
    @staticmethod
    def find_by_name(name):
        u = User()
        u.name = name
        u.log_file = os.path.join(User.base_path,u.name,'file_status.log')
        u.sync_path = os.path.join(User.base_path,u.name,'sync')
        return u

