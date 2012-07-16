# Readme #

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

There isn't really anything to install on the server as far as rainmaker is concerned, but you do need to have unison and an openssh-server setup and ready to go.

### Ubuntu ###
Tested on 12.04 Desktop
~~~
sudo apt-get install openssh-client openssh-server unison
~~~

###Windows:###
Coming Soon
###Mac OSx:###
Coming Soon

## Development Notes: ##
* Unison allows multiple path statements in the command line!
** This is important because it will allow us to update multiple files per connection

