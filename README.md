#rainmaker #
## About ##

Rainmaker is a qt4/python wrapper for unison that aims to provide a simple way of providing a bidirectional file synchronization service. Rainmaker uses the python watchdog library to gain cross platform FSMonitoring capabilities. Because of this you only need to do a full sync when you start rainmaker. Afterwards the watchdog filesystem monitor will track the changes that occur within your sync directory and only invoke unison to update them when there is a change.

The UI is not yet fully functional, but feel free to poke around. To start the client you first need to:
* Change some of the configuration options in ./client/conf
* Make sure you have unison, an ssh-client, python, python-watchdog, python-yaml installed
* The python-pip package makes installing yaml and watchdog a breeze
* execute the following in a terminal:
~~~
python ./watcher.py
~~~




**Be sure that you install the same version of unison on all clients and the server**

## Client Install: ##
### Ubuntu ###

From a terminal run the following commands
~~~
# Some day we might take care of these steps in an installer

# Install unison and ssh-client
sudo apt-get install unison openssh-client python-pip

# Install python libraries 
sudo pip install watchdog
sudo pip install yaml

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
sudo apt-get install apparmor-utils

~~~

###Windows:###
Coming Soon
###Mac OSx:###
Coming Soon

## Development Notes: ##
* Unison allows multiple path statements in the command line!
    * This is important because it will allow us to update multiple files per connection

