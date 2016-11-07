#!/usr/bin/python3

# TEMP
from pprint import pprint

import getch
import github3
import http.client
import os
import re
import requests
import shutil
import signal
import subprocess
import sys
import termcolor
import tempfile
import time
import traceback
import urllib.request

class Error(Exception):
    """Exception raised for errors."""
    pass

# submit50
def main():

    # listen for ctrl-c
    signal.signal(signal.SIGINT, handler)

    # check for git
    if not shutil.which("git"):
        sys.exit("Missing dependency. Install git.")

    # submit50 -h
    # submit50 --help
    if len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        usage()

    # submit50 --checkout
    elif sys.argv[1] == "--checkout":
        checkout(sys.argv[1:])

    # submit50 problem
    elif len(sys.argv) == 2:
        submit(sys.argv[1])

    # submit50 *
    else:
        usage()
        sys.exit(1)

    # kthxbai
    sys.exit(0)

def authenticate():
    """TODO"""

    # prompt for username
    while True:
        print("GitHub username: ", end="", flush=True)
        username = input().strip()
        if username:
            break

    # prompt for password
    while True:
        print("GitHub password: ", end="", flush=True)
        password = str()
        while True:
            ch = getch.getch()
            if ch == "\n": # Enter
                print()
                break
            elif ch == "\177": # DEL
                if len(password) > 1:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
            else:
                password += ch
                print("*", end="", flush=True)
        if password:
            break

    # authenticate user
    github = github3.login(username, password, two_factor_callback=two_factor_callback)
    user = github.me()
    username = user.login
    email = "{}@users.noreply.github.com".format(user.login)
    return (username, password, email)

def call(args, stdin=None):
    """Run the command described by args. Return output as str."""
    call.process = subprocess.Popen(
        args,
        shell=True,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    try:
        stdout_data = call.process.communicate(stdin)[0]
        returncode = call.process.returncode
        call.process = None
        return stdout_data if returncode == 0 else None
    except subprocess.TimeoutExpired:
        proc.kill()
        call.process = None
        return None
call.process = None

def excepthook(type, value, tb):
    """Report an exception."""
    if type is Error:
        if str(value):
            print(termcolor.colored(str(value), "yellow"))
    elif type is github3.GitHubError:
        print(termcolor.colored(value.message, "yellow"))
    else:
        traceback.print_tb(tb)
        print(termcolor.colored("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "yellow"))
    print(termcolor.colored("Submission cancelled.", "red"))
sys.excepthook = excepthook

def handler(number, frame):
    """Handle SIGINT."""
    if call.process:
        call.process.kill()
    print()
    sys.exit(0)

def submit(problem):
    """Submit problem."""

    # ensure problem exists
    _, EXCLUDE = tempfile.mkstemp()
    url = "https://raw.githubusercontent.com/submit50/submit50/{}/exclude?{}".format(problem, time.time())
    try:
        urllib.request.urlretrieve(url, filename=EXCLUDE)
        lines = open(EXCLUDE)
    except Exception as e:
        print(e)
        raise Error("Invalid problem. Did you mean to submit something else?") from None
    missing = []
    for line in lines:
        matches = re.match(r"^\s*#\s*([^\s]+)\s*$", line)
        if matches:
            pattern = matches.group(1)
            if pattern[:-1] == "/":
                if not os.path.isdir(pattern):
                    missing.append(pattern)
            else:
                if not os.path.isfile(pattern):
                    missing.append(pattern)
    if missing:
        print("You seem to be missing these files:")
        for pattern in missing:
            print(" {}".format(pattern))
        print("Proceed anyway? ", end="")
        if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
            raise Error()

    exit(0)

    #
    try:
        username, password, email = authenticate()
    except:
        raise Error("Invalid username and/or password.") from None

    # TEMP
    github = github3.login(username, password, two_factor_callback=two_factor_callback)

    #
    repository = github.repository("submit50", username)
    if not repository:
        raise Error("Looks like we haven't enabled submit50 for your account yet! Let sysadmins@cs50.harvard.edu know your GitHub username!")

    #
    run("git clone --bare {} {}".format(
        shlex.quote("https://{}@github.com/submit50/{}".format(username, username)),
        shlex.quote(GIT_DIR)
    ))

    run("git config user.email {}".format(shlex.quote(email)))
    run("git config user.name {}".format(shlex.quote(username)))

    run("git symbolic-ref HEAD {}".format(shlex.quote("refs/heads/{}".format(problem))))

    run("git config core.excludesFile {}".format(shlex.quote(exclude)))

def run(command, password=None):
    if password:
        child = pexpect.spawnu(command, env={
            "GIT_DIR": run.GIT_DIR, "GIT_WORK_TREE": run.GIT_WORK_TREE
        })
        child.logfile_read = sys.stdout
        child.expect("Password.*:")
        child.sendline(password)
        child.expect(pexpect.EOF) # TODO: add try/except?
        child.close()
    else:
        pexpect.run(command)
run.GIT_DIR = tempfile.mkdtemp() # TODO: what if this ends up in CWD?
run.GIT_WORK_TREE = os.getcwd()

def two_factor_callback():
    """Get one-time authentication code."""
    while True:
        print("Authentication Code: ", end="", flush=True)
        code = input()
        if code:
            break
    return code

def usage():
    print("Usage: submit50 problem")

if __name__ == "__main__":
    main()
