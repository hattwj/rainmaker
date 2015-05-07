# Todo Items:

* Application is in pre-alpha status
* from types import MethodType
    - tox and controllers

# Ideas:

- twisted for tcp/udp/tox
    - problem with nose and twisted
    - problem with sqlalchemy and twisted
    
- asyncio for tcp/udp
    - need cert implemented
    - reimplement udp
    - need protocol(like Amp)
    
- tox for everything
    - slow because of tox (maybe)
    - supports file transfers (usually possibly direct)
    - encrypted
    - easy
    - high CPU usage

Strategy:
    - Tox update thread
    - Watchdog thread
    - Database thread
    - File system scanner thread
