#rainmaker #
## About ##

Rainmaker is a qt4/python wrapper for unison that aims to provide a simple way of providing a bidirectional file synchronization service. Rainmaker uses the python watchdog library to gain cross platform FSMonitoring capabilities. Because of this you only need to do a full sync when you start rainmaker. Afterwards the watchdog filesystem monitor will track the changes that occur within your sync directory and only invoke unison to update them when there is a change.

The UI is not yet fully functional, but feel free to poke around. To start the client you first need to:
* Change some of the configuration options in ./client/conf
* Make sure you have unison, an ssh-client, python, python-watchdog, python-yaml installed
* The python-pip package makes installing yaml and watchdog a breeze
* execute the following in a terminal:

~~~

#The first thing to do after installing the client is to create a profile. The
#following command will gather the required information to create a profile.
python ./rainmaker -c

# once you have created a profile you can start up rainmaker and begin syncing your files
# by default profiles are configured to automatically start syncing when you start rainmaker
python ./rainmaker.py

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

There isnt really anything to install on the server as far as rainmaker is concerned, but you do need to have unison and an openssh-server setup and ready to go.
Server side changes will be supported soon.

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

##Client Usage##

Not all features are implemented

~~~
usage: rainmaker.py [-h] [-v] [-d PROFILE] [--start PROFILE] [--stop PROFILE]
                    [-t PROFILE] [-a] [-q] [--log {warn,info,debug,False}]
                    [-c] [-l] [-u [PROFILE]]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d PROFILE, --delete PROFILE
  --start PROFILE
  --stop PROFILE
  -t PROFILE, --test PROFILE
  -a, --auto
  -q, --quiet
  --log {warn,info,debug,False}
  -c                    [TYPE] [OPTIONS]
  -l                    List all profiles or list settings for specicific
                        profile
  -u [PROFILE]          [PROFILE] [OPTIONS]
~~~

## Development Notes: ##
* Unison allows multiple path statements in the command line!
    * This is important because it will allow us to update multiple files per connection

