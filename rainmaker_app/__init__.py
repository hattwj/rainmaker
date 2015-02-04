
from twisted.internet import reactor

from .lib.attrs_bag import AttrsBag
version = '0.0.2'

app = AttrsBag()
app.reactor = reactor
app.start_console = False
app.tox_settings = {}
#from .boot import pre_init
