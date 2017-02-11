#!/usr/bin/python3

import argparse
import datetime
import getch
import http.client
import itertools
import json
import os
import pexpect
import re
import requests
import select
import shlex
import shutil
import signal
import subprocess
import sys
import termcolor
import tempfile
import time
import traceback
import urllib.request

from distutils.version import StrictVersion
from threading import Thread

EXCLUDE = None
ORG_NAME = "submit50"
VERSION = "2.1.0"
timestamp = ""

class Error(Exception):
    """Exception raised for errors."""
    pass

# submit50
def main():

    # listen for ctrl-c
    signal.signal(signal.SIGINT, handler)

    # check for version
    res = requests.get("https://cs50.me/submit50-version/")
    if res.status_code != 200:
        raise Error("You have an unknown verison of submit50. Email sysadmins@cs50.harvard.edu.") from None
    version_required = res.text.strip()
    if StrictVersion(version_required) > StrictVersion(VERSION):
        raise Error("You have an old version of submit50. Run update50, then re-run submit50!") from None

    # compute timestamp
    headers = requests.get("https://api.github.com/").headers
    global timestamp
    timestamp = datetime.datetime.strptime(headers["Date"], "%a, %d %b %Y %H:%M:%S %Z")
    timestamp = timestamp.strftime("%Y%m%dT%H%M%SZ")

    # check for git
    if not shutil.which("git"):
        sys.exit("Missing dependency. Install git.")

    # define command-line arguments
    parser = argparse.ArgumentParser(prog="submit50", add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-c", "--checkout", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("args", nargs="*")
    args = vars(parser.parse_args())

    # submit50 -v
    # submit50 --verbose
    if args["verbose"]:
        run.verbose = True

    # submit50 -h
    # submit50 --help
    if (len(args["args"]) == 0 and not args["checkout"]) or args["help"]:
        usage()

    # submit50 -c
    # submit50 --checkout
    elif args["checkout"]:
        checkout(args["args"])

    # submit50 problem
    elif len(args["args"]) == 1:
        submit(args["args"][0])

    # submit50 *
    else:
        usage()
        sys.exit(1)

    # kthxbai
    sys.exit(0)

def authenticate():
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
                if len(password) > 0:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
            else:
                password += ch
                print("*", end="", flush=True)
        if password:
            break

    # authenticate user
    two_factor.auth = (username, password)
    email = "{}@users.noreply.github.com".format(username)
    res = requests.get("https://api.github.com/user", auth=(username, password))

    # check for 2-factor authentication
    # http://github3.readthedocs.io/en/develop/examples/oauth.html?highlight=token
    if "X-GitHub-OTP" in res.headers:
        two_factor()
        password = two_factor.token
    # check if incorrect password
    elif res.status_code == 401:
        raise Error("Invalid username and/or password.") from None
    elif res.status_code != 200:
        raise Error("Could not authenticate user.") from None

    return (username, password, email)

def excepthook(type, value, tb):
    """Report an exception."""
    teardown()
    if type is Error and str(value):
        print(termcolor.colored(str(value), "yellow"))
    else:
        if run.verbose:
            traceback.print_tb(tb)
        print(termcolor.colored("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "yellow"))
    print(termcolor.colored("Submission cancelled.", "red"))
sys.excepthook = excepthook

def handler(number, frame):
    """Handle SIGINT."""
    teardown()
    print()
    sys.exit(0)

def submit(problem):
    """Submit problem."""

    # assume cs50/ problem if problem name begins with a year
    if problem.split("/")[0].isdigit():
        problem = os.path.join("cs50", problem)

    # ensure problem exists
    global EXCLUDE
    _, EXCLUDE = tempfile.mkstemp()
    url = "https://cs50.me/excludes/{}/".format(problem)
    try:
        urllib.request.urlretrieve(url, filename=EXCLUDE)
        lines = open(EXCLUDE)
    except Exception as e:
        print(e)
        raise Error("Invalid problem. Did you mean to submit something else?") from None

    # check for missing files
    missing = []
    for line in lines:
        matches = re.match(r"^\s*#\s*([^\s]+)\s*$", line)
        if matches:
            pattern = matches.group(1)
            if pattern[:-1] == "/":
                if not os.path.isdir(pattern):
                    missing.append(pattern)
            elif not os.path.isfile(pattern):
                missing.append(pattern)
    if missing:
        print("You seem to be missing these files:")
        for pattern in missing:
            print(" {}".format(pattern))
        raise Error("Ensure you have the required files before submitting.") from None

    # authenticate user
    username, password, email = authenticate()

    # show the spinner
    if not run.verbose:
        spin.keep_spinning = True
        thread = Thread(target=spin, args=("Logging in... ",))
        thread.start()

    # check for submit50 repository
    res = requests.get("https://api.github.com/repos/{}/{}".format(ORG_NAME, username), auth=(username, password))
    repository = res.status_code == 200
    if not repository:
        raise Error("Looks like we haven't enabled submit50 for your account yet! Let sysadmins@cs50.harvard.edu know your GitHub username!")

    # clone submit50 repository
    run("git clone --bare {} {}".format(
        shlex.quote("https://{}@github.com/{}/{}".format(username, ORG_NAME, username)), shlex.quote(run.GIT_DIR)),
        password=password)

    # set options
    branch = problem
    tag = "{}@{}".format(branch, timestamp)
    run("git config user.email {}".format(shlex.quote(email)))
    run("git config user.name {}".format(shlex.quote(username)))
    run("git symbolic-ref HEAD refs/heads/{}".format(shlex.quote(branch)))

    # patterns of file names to exclude
    run("git config core.excludesFile {}".format(shlex.quote(EXCLUDE)))
    run("git config core.ignorecase true")

    # adds, modifies, and removes index entries to match the working tree
    run("git add --all")

    # get file lists
    files = run("git ls-files").decode("utf-8").split()
    other = run("git ls-files --other").decode("utf-8").split()

    # stop the spinner
    if not run.verbose:
        spin.keep_spinning = False
        thread.join()

    # files that will be submitted
    if len(files) == 0:
        raise Error("None of the files in this directory are expected for submission.") from None
    print(termcolor.colored("Files that will be submitted:", "yellow"))
    for f in files:
        print(" {}".format(termcolor.colored(f, "yellow")))

    # files that won't be submitted
    if len(other) != 0:
        print(termcolor.colored("Files that won't be submitted:", "yellow"))
        for f in other:
            print(" {}".format(termcolor.colored(f, "yellow")))

    print("Keeping in mind the course's policy on academic honesty, are you sure you want to submit these files? ", end="")
    if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
        raise Error("No files were submitted.") from None

    # show the spinner
    if not run.verbose:
        spin.keep_spinning = True
        thread = Thread(target=spin)
        thread.start()

    # push changes
    run("git commit --allow-empty --message='{}'".format(timestamp))
    run("git push origin 'refs/heads/{}'".format(branch), password=password)

    # create a new orphan branch and switch to it
    run("git checkout --orphan 'orphan'")
    run("git add --all")
    run("git commit --allow-empty --message='{}'".format(timestamp))

    # add a tag reference
    run("git tag --force '{}'".format(tag))
    run("git push --force origin 'refs/tags/{}'".format(tag), password=password)

    # stop the spinner
    if not run.verbose:
        spin.keep_spinning = False
        thread.join()

    # successful submission
    teardown()
    print(termcolor.colored("Submitted {}!\nSee https://github.com/{}/{}/tree/{}.".format(
        problem, ORG_NAME, username, branch), "green"))

def checkout(args):
    usernames = None
    problem = None

    # detect piped usernames
    # http://stackoverflow.com/a/17735803
    if not sys.stdin.isatty():
        usernames = []
        for line in sys.stdin:
            usernames.append(line.strip())

    if len(args) == 0 and usernames == None:
        print("Usage: submit50 --checkout [problem] [@username ...]")
        sys.exit(1)

    if len(args) > 0:
        # check if problem is specified
        if args[0].startswith("@") and usernames == None:
            usernames = args
        else:
            problem = args[0]
            if usernames == None and len(args) > 1:
                usernames = args[1:]

    # authenticate user
    try:
        username, password, email = authenticate()
    except:
        raise Error("Invalid username and/or password.") from None

    # get student names if none provided
    if usernames == None:
        usernames = []
        repos = requests.get("https://api.github.com/orgs/{}/repos?per_page=100".format(ORG_NAME), auth=(username, password))
        for repo in repos.json():
            if repo["name"] != ORG_NAME:
                usernames.append(repo["name"])

    # clone repositories
    for name in usernames:
        name = name.replace("@", "")

        # check whether name exists in filesystem
        if os.path.exists(name):

            # check whether name is a directory
            if os.path.isfile(name):
                print("Not a directory: {}".format(name))
                continue

            # pull repository
            url = run("git config --get remote.origin.url", cwd=name, env={}).decode("utf-8")
            if url == "":
                print("Missing origin: {}".format(name))
                continue
            if not url.startswith("https://{}@github.com/{}/".format(username, ORG_NAME)):
                print("Invalid repo: {}".format(name))
            run("git pull", cwd=name, env={})
        else:
            # clone repository if it doesn't already exist
            run("git clone 'https://{}@github.com/{}/{}' '{}'".format(username, ORG_NAME, name, name), password=password, env={})

        # if no problem specified, don't switch branches
        if problem == None:
            continue

        # check out branch
        branches = run("git branch -r", cwd=name, env={}).decode("utf-8")
        if "origin/{}".format(problem) in branches:
            branches = run("git branch", cwd=name, env={}).decode("utf-8")
            if problem in branches:
                run("git checkout '{}'".format(problem), cwd=name, env={})
            else:
                run("git checkout --track 'origin/{}'".format(problem), cwd=name, env={})
        else:
            branches = run("git branch", cwd=name, env={}).decode("utf-8")
            if problem in branches:
                run("git checkout '{}'".format(problem), cwd=name, env={})
            else:
                run("git checkout -b '{}'".format(problem), cwd=name, env={})
                run("git rm -rf .", cwd=name, env={})

    teardown()

def run(command, password=None, cwd=None, env=None):
    """Run a command."""
    if run.verbose:
        print(command)

    # when not using --checkout, include GIT_DIR and GIT_WORK_TREE in env
    if env == None:
        env = {
            "GIT_DIR": run.GIT_DIR,
            "GIT_WORK_TREE": run.GIT_WORK_TREE
        }

    # if authentication required for command, send password when requested
    if password:
        child = pexpect.spawnu(command, env=env, cwd=cwd)

        # send output of command to stdout only if run with --verbose
        if run.verbose:
            child.logfile_read = sys.stdout

        try:
            child.expect("Password.*:")
            child.sendline(password)
            child.expect(pexpect.EOF)
        except:
            pass
        child.close()
        if child.exitstatus != 0:
            raise Error()
    else:
        output, status = pexpect.run(command, env=env, cwd=cwd, withexitstatus=True)
        # check exit status of command
        if status != 0:
            raise Error()
        return output
run.GIT_DIR = tempfile.mkdtemp()
run.GIT_WORK_TREE = os.getcwd()
run.verbose = False

def teardown():
    """Delete temporary directory and temporary file."""
    spin.keep_spinning = False
    pexpect.run("rm -rf '{}'".format(run.GIT_DIR))
    if EXCLUDE:
        pexpect.run("rm -f '{}'".format(EXCLUDE))

def two_factor():
    """Get one-time authentication code."""
    # send authentication request
    requests.post("https://api.github.com/authorizations", auth=two_factor.auth)
    while True:
        print("Authentication Code: ", end="", flush=True)
        code = input()
        if code:
            break
    data = json.dumps({"scopes":["repo", "user"], "note":"{} {}".format(ORG_NAME, timestamp)})
    res = requests.post("https://api.github.com/authorizations", auth=two_factor.auth,
        data=data,
        headers={"X-GitHub-OTP": str(code)})
    if res.status_code == 201 and "token" in res.json():
        two_factor.token = res.json()["token"]
    else:
        raise Error("Could not complete two-factor authentication.") from None
    return code
two_factor.auth = None
two_factor.token = None

def spin(message="Submitting... "):
    spinner = itertools.cycle(["-", "\\", "|", "/"])
    sys.stdout.write(message)
    sys.stdout.flush()
    while spin.keep_spinning:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write("\b")
        time.sleep(0.05)
    sys.stdout.write("\r")
    sys.stdout.flush()
spin.keep_spinning = True

def usage():
    """Print usage."""
    print("Usage: submit50 problem")

if __name__ == "__main__":
    main()
