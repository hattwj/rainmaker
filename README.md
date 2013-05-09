#rainmaker #

## About ##

Rainmaker aims to provide a simple bidirectional file synchronization service by using common programs already installed on most computers. Rainmaker uses the python watchdog library to gain cross platform FSMonitoring capabilities, and utilizes Unison for file transfer. Because of the watchdog library you only need to do a full sync when you start rainmaker. Afterwards the watchdog filesystem monitor will track the changes that occur within your sync directory and only invoke unison to update them when there is a change.

### Features ###

* Remote file system events
* No central server required

### Known Issues ###

* GUI is not functional
* No desktop notifications

## Getting Started ##

The first thing to do after installing the client is to create a profile. The
following command will gather the required information to create a profile.

~~~
./rainmaker create
~~~

Once you have created a profile you can start up rainmaker and begin syncing your files.
By default profiles are configured to automatically start syncing when you start rainmaker

~~~
./rainmaker
~~~

### Client Usage ###

Not all features are implemented

~~~bash
usage: rainmaker [-h] [-q] [-v] [--user-dir USER_DIR]
                 [--log {debug,info,warn,error,none}]
                 [{create,delete,daemon,list,update,start,auto,info}]

positional arguments:
  {create,delete,daemon,list,update,start,auto,info}
                        Action to perform: (default="auto")
                        auto    -   Start profiles where 'auto' = True
                        daemon  -   Start all daemon profiles.
                                    Only log file system events.
                        create  -   Create a new profile
                        delete  -   Delete a profile
                        list    -   List all profiles, or specific
                                    information about a single profile
                        update  -   Update the contents of a profile
                        start   -   Only run the specified profile(s)
                        info    -   Display config information

optional arguments:
  -h, --help            show this help message and exit
  -q                    Quiet. Suppress output
  -v                    Verbosity level, -vvvv is max verbosity
  --user-dir USER_DIR   Location of app data (default="~/.rainmaker")
  --log {debug,info,warn,error,none}
                        Log level

~~~

**Be sure that you install the same version of unison on all clients and the server**

## Client Install: ##

### Ubuntu ###

From a terminal run the following commands

~~~bash

# Some day we might take care of these steps in an installer

# Install unison and ssh-client
sudo apt-get install unison openssh-client python-pip python-yaml

# Install python libraries 
sudo pip install watchdog

# Create a rainmaker only ssh-key
ssh-keygen -f rainamker -t rsa -b 2048 -C "SSH Key for rainmaker"

~~~

Now you should be ready to run rainmaker


###Windows:###

Coming Soon

###Mac OSx:###

Coming Soon

## Server Install: ##

There isn't really anything to install on the server as far as rainmaker is concerned, but you do need to have unison and an openssh-server setup and ready to go.

### Ubuntu ###

Tested on 12.04 Desktop

~~~bash

# Install software

sudo apt-get install openssh-client openssh-server unison

# Create rainmaker user to manage all sync connections

sudo adduser rainmaker --disabled-password

# Add keys to rainmaker user authorized keys files
# See Client Install Section

# Add SELinux/AppArmor restrictions for unison
# not yet implemented, needed for untrusted clients
sudo apt-get install apparmor-utils

~~~

###Windows:###

Coming Soon

###Mac OSx:###

Coming Soon


## Development Notes: ##

Server side events are now supported!

See [TODO](TODO.md) for other notices

## References ##

* [Unison] (http://www.cis.upenn.edu/~bcpierce/unison/)
* [OpenSSH] (http://www.openssh.org/)
* [Watchdog] (http://packages.python.org/watchdog/)

