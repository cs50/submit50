#!/bin/bash

# install dependencies
apt-get install python3-pexpect python3-termcolor
pip3 install getch

# ensure dependencies are readable
chmod a+r /usr/local/lib/python3.4/dist-packages/getch.cpython-34m.so
chmod a+r /usr/local/lib/python3.4/dist-packages/termcolor.py
chmod -R a+rX /usr/local/lib/python3.4/dist-packages/pexpect/

# ensure submit50 is executable
chmod -R a+rX /opt/cs50/submit50
chmod -R a+x /opt/cs50/submit50/bin/*

# install submit50 in /opt/cs50/bin
umask 0022
mkdir -p /opt/cs50/bin
ln -s /opt/cs50/submit50/bin/submit50.py /opt/cs50/bin/submit50
