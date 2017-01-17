#!/bin/bash

# install dependencies
umask 0022
pip3 install getch

# ensure submit50 is executable
chmod -R a+rX /opt/cs50/submit50
chmod -R a+x /opt/cs50/submit50/bin/*

# install submit50 in /opt/cs50/bin
mkdir -p /opt/cs50/bin
ln -s /opt/cs50/submit50/bin/submit50.py /opt/cs50/bin/submit50
