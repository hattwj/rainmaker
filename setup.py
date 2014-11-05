from setuptools import setup

setup(name='rainmaker',
    version='0.0.2',
    description='',
    url='http://github.com/hattwj/rainmaker',
    author='William Hatt',
    author_email='hattwj@yahoo.com',
    license='MIT',
    packages=['rainmaker_app'],
    install_requires=[
        'passlib',
        'watchdog',
        'twisted',
        'twistar',
        'ishell',
        'pyyaml'           
    ],
    zip_safe=False)
