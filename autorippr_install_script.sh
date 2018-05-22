#!/bin/bash

set -x

# Install Script Version 1.0
# This script is designed to install Autorippr for Ubuntu 16.04 LTS
# All required dependancies and packages will be installed
# Packages that are installed:
# --GIT
# --Makemkv
# --Python Dev Tools
# --Python Dependancies for Autorippr
# --PIP
# --Handbrake-CLI
# --Filebot
# --Autorippr

MAKEMKV_VERSION=1.10.2

# Change to execution directory
cd ~

# Ubuntu 16.04 Error fix for installing packages
sudo apt-get purge runit
sudo apt-get purge git-all
sudo apt-get purge git
sudo apt-get autoremove
sudo apt update

# Install Git
sudo apt install git 

#Install PIP
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

#Intall MakeMKV required tools and libraries
sudo apt-get install build-essential pkg-config libc6-dev libssl-dev libexpat1-dev libavcodec-dev libgl1-mesa-dev libqt4-dev

#Install MakeMKV
wget http://www.makemkv.com/download/makemkv-bin-${MAKEMKV_VERSION}.tar.gz
wget http://www.makemkv.com/download/makemkv-oss-${MAKEMKV_VERSION}.tar.gz
tar -zxmf makemkv-oss-${MAKEMKV_VERSION}.tar.gz
tar -zxmf makemkv-bin-${MAKEMKV_VERSION}.tar.gz
cd makemkv-oss-${MAKEMKV_VERSION}
./configure
make
sudo make install
cd ..
cd makemkv-bin-${MAKEMKV_VERSION}
make
sudo make install

# Install Handbrake CLI
sudo apt-get install handbrake-cli

# Python update to enable next step
sudo apt-get install python-dev

# Install Java prerequisite for Filebot
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer

# Install Filebot
if [ `uname -m` = "i686" ]
then
   wget -O filebot-i386.deb 'http://filebot.sourceforge.net/download.php?type=deb&arch=i386'
else
   wget -O filebot-amd64.deb 'http://filebot.sourceforge.net/download.php?type=deb&arch=amd64'
fi
sudo dpkg --force-depends -i filebot-*.deb && rm filebot-*.deb

# Install Python Required Packages
sudo pip install tendo pyyaml peewee pushover pymediainfo 

# Install Autorippr
cd ~
git clone https://github.com/JasonMillward/Autorippr.git
cd Autorippr
git checkout
cp settings.example.cfg settings.cfg

# Verification Test
python autorippr.py --test

# Completion Message
echo " "
echo "###################################################"
echo "##            Install Complete!                  ##"
echo "##      Update: ~/Autorippr/settings.cfg         ##"
echo "###################################################"
