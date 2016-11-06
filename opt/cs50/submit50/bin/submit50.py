#!/usr/bin/python3

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

class Error(Exception):
    """Exception raised for errors."""
    pass

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

def credentials():
    """Return username and password."""

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

    # return credentials
    return username, password

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
    url = "https://raw.githubusercontent.com/submit50/submit50/{}/exclude?{}".format(problem, time.time())
    try:
        response = urllib.request.urlopen(url)
        exclude = response.read().decode(response.headers.get_content_charset("utf-8")).splitlines()
    except:
        raise Error("Invalid problem. Did you mean to submit something else?") from None
    missing = []
    for line in exclude:
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

    # prompt for credentials
    username, password = credentials()

    #
    #r = requests.get("https://api.github.com/repos/submit50/{}".format(username))

    #
    github = github3.login(username, password, two_factor_callback=two_factor_callback)

    #
    repository = github.repository("submit50", username)
    if not repository:
        raise Error("Looks like we haven't enabled submit50 for your account yet! Let sysadmins@cs50.harvard.edu know your GitHub username!")

    GIT_DIR = tempfile.mkdtemp() # TODO: what if this ends up in CWD?
    GIT_WORK_TREE = os.getcwd()


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
