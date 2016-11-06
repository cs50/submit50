#!/usr/bin/env python3

import pexpect
import tempfile
import sys

GIT_DIR = tempfile.mkdtemp()

username = "student50"
password = "test1test"


# spawn git clone --bare "https://$username@github.com/submit50/$username" "$GIT_DIR"
child = pexpect.spawnu(
    "git clone --bare \"https://{}@github.com/submit50/{}\" \"{}\"".format(
        username, username, GIT_DIR
    )
)
child.logfile_read = sys.stdout
child.expect("Password.*:")
child.sendline(password)
child.expect(pexpect.EOF)
child.close()
