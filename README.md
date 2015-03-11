#rainmaker #

## About ##

Rainmaker aims to provide a simple bidirectional file synchronization service. Rainmaker uses the python watchdog library to gain cross platform FSMonitoring capabilities, and utilizes Twisted for file transfer. Because of the watchdog library you only need to do a full sync when you start rainmaker. Afterwards the watchdog filesystem monitor will track the changes that occur within your sync directory and only invoke syncronizations when there is a file system event.

### Planned Features ###

* Monitor file system events
* No central server required
* Distributed architecture

### Known Issues ###

* Does not work
* Still under heavy development


See [TODO](TODO.md) for other notices

## Inspiration ##

* [Tox] (https://github.com/Tox)
* [Unison] (http://www.cis.upenn.edu/~bcpierce/unison/)
* [OpenSSH] (http://www.openssh.org/)
* [Watchdog] (http://packages.python.org/watchdog/)


# Quick Start #

## Ubuntu Dependencies ##

```bash
# Compilation dependencies
sudo apt-get install build-essential libtool autotools-dev automake checkinstall check git yasm
```

## Compile Tox ##

```bash
# Compile and install libsodium
git clone git://github.com/jedisct1/libsodium.git
cd libsodium
git checkout tags/1.0.0
./autogen.sh
./configure && make check
sudo checkinstall --install --pkgname libsodium --pkgversion 1.0.0 --nodoc
sudo ldconfig
cd ..

# Compile and Install Tox
git clone git://github.com/irungentoo/toxcore.git
cd toxcore
autoreconf -i
./configure
make
sudo make install
cd ..

```

## Install pip packages ##
```bash
# pip install
sudo pip3 install -r ./requirements.txt

# ldconfig fix
sudo ldconfig

```

