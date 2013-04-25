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

once you have created a profile you can start up rainmaker and begin syncing your files.
By default profiles are configured to automatically start syncing when you start rainmaker
~~~
./rainmaker
/~~~

###Client Usage###

Not all features are implemented

~~~
usage: rainmaker [-h] [-v] [-q] [--log {debug,info,warn,error,none}]
                 [{create,delete,list,update,start,auto,info}]

positional arguments:
  {create,delete,list,update,start,auto,info}
                        Action to perform (default="auto")
                        
                        auto    -   Start all profiles where 'auto' = True
                        
                        create  -   Create a new profile
                        
                        delete  -   Delete a profile
                        
                        list    -   List all profiles or specific
                                    information about a single profile
                        
                        update  -   Update the contents of a profile
                        
                        start   -   Start by running the specified profile
                        
                        info    -   Display config information and exit

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -q                    Suppress all output.
  --log {debug,info,warn,error,none}
                        Set log level
~~~


**Be sure that you install the same version of unison on all clients and the server**

## Client Install: ##
### Ubuntu ###

From a terminal run the following commands
~~~
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
~~~
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
* Unison allows multiple path statements in the command line!
    * This is important because it will allow us to update multiple files per connection

##References##
* [Unison] (http://www.cis.upenn.edu/~bcpierce/unison/)
* [OpenSSH] (http://www.openssh.org/)
* [Watchdog] (http://packages.python.org/watchdog/)
