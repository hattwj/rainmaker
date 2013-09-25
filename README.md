#rainmaker #

## About ##

Rainmaker aims to provide a simple bidirectional file synchronization service. Rainmaker uses the python watchdog library to gain cross platform FSMonitoring capabilities, and utilizes Twisted for file transfer. Because of the watchdog library you only need to do a full sync when you start rainmaker. Afterwards the watchdog filesystem monitor will track the changes that occur within your sync directory and only invoke syncronizations when there is a file system event.

### Planned Features ###

* Monitor file system events
* No central server required
* Distributed architecture

### Known Issues ###

* Still under heavy development


See [TODO](TODO.md) for other notices

## References ##

* [Unison] (http://www.cis.upenn.edu/~bcpierce/unison/)
* [OpenSSH] (http://www.openssh.org/)
* [Watchdog] (http://packages.python.org/watchdog/)

