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
