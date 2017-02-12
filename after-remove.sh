#!/bin/bash

# remove /opt/cs50/bin/submit50 and any empty parents
rm -f /opt/cs50/bin/submit50
rm -df /opt/cs50/bin /opt/cs50 >/dev/null 2>&1 || true
