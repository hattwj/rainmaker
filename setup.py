try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'rainmaker',
    'author': 'William Hatt',
    'url': 'github.com/hattwj/rainmaker.git',
    'download_url': 'Where to download it.',
    'author_email': 'My email.',
    'version': '0.3',
    'install_requires': ['nose', 'twisted', 'watchdog', 'PyTox'],
    'packages': ['rainmaker'],
    'scripts': [],
    'name': 'rainmaker'
}

setup(**config)
