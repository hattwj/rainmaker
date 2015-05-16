# Todo Items:

- Interactive console
    - Add / remove syncs from command line
- Complete work on send receive file ability
- SqlAlchemy DB triggers to trigger sync events and downloads


# Ideas:

## Strategy:

- pytox for everything
    - slow because of tox (maybe)
    - supports file transfers (usually possibly direct)
    - encrypted
    - easy to implement
    - high CPU usage

- Threading
    - Tox update thread
    - Watchdog thread
    - Database thread
    - File system scanner thread

## Mixins in python

```python
# This is useful for tox and controllers
from types import MethodType
```

## Control access to database ##

```python

from concurrent.futures import ThreadPoolExecutor
db_man = ThreadPoolExecutor(max_workers=1)
db_man.submit(my_func)


```

## Application event counter ##

Count events, not time
    - Get latest time at startup
    - Increment counter on event
    - Set updated_at, created_at on save / update

