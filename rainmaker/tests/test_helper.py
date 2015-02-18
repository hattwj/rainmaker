import os

from rainmaker.main import Application

temp_root = os.path.abspath(
    os.path.join(os.path.dirname(
        __file__),
        '..',
        '..',
        'tmp'))
Application.user_root = temp_root
