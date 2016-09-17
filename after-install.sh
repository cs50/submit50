#!/bin/bash

# ensure submit50 is executable
chmod -R a+rX /opt/cs50/submit50
chmod -R a+x /opt/cs50/submit50/bin/*

# install submit50 in /op/cs50/bin
umask 0022
mkdir -p /opt/cs50/bin
ln -s /opt/cs50/submit50/bin/submit50 /opt/cs50/bin/submit50
