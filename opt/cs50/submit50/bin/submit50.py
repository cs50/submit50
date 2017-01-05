#!/usr/bin/python3

import datetime
import getch
import github3
import http.client
import os
import pexpect
import pytz
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

ORG_NAME = "submit50"
EXCLUDE = None

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
        checkout(sys.argv[2:])

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
    two_factor_callback.auth = (username, password)
    github = github3.login(username, password, two_factor_callback=two_factor_callback)
    email = "{}@users.noreply.github.com".format(username)
    return (username, password, email, github)

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
        call.process.kill()
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
    teardown()
    print(termcolor.colored("Submission cancelled.", "red"))
# sys.excepthook = excepthook

def handler(number, frame):
    """Handle SIGINT."""
    if call.process:
        call.process.kill()
    print()
    sys.exit(0)

def submit(problem):
    """Submit problem."""

    # get the current time, convert to EST
    headers = requests.get("https://api.github.com/").headers
    timestamp = datetime.datetime.strptime(headers["Date"], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=pytz.utc)
    timestamp = timestamp.astimezone(pytz.timezone("America/New_York")).strftime("%a, %d %b %Y %H:%M:%S %Z")

    # ensure problem exists
    global EXCLUDE
    _, EXCLUDE = tempfile.mkstemp()
    url = "https://raw.githubusercontent.com/{0}/{0}/{1}/exclude".format(ORG_NAME, problem)
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
        print("Proceed anyway? ", end="")
        if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
            raise Error()

    # authenticate user
    try:
        username, password, email, github = authenticate()
    except:
        raise Error("Invalid username and/or password.") from None

    # check for submit50 repository
    repository = github.repository(ORG_NAME, username)
    if not repository:
        raise Error("Looks like we haven't enabled submit50 for your account yet! Let sysadmins@cs50.harvard.edu know your GitHub username!")

    # clone submit50 repository
    run("git clone --bare {} {}".format(
        shlex.quote("https://{}@github.com/{}/{}".format(username, ORG_NAME, username)),
        shlex.quote(run.GIT_DIR)
    ))

    # set options
    run("git config user.email {}".format(shlex.quote(email)))
    run("git config user.name {}".format(shlex.quote(username)))
    run("git symbolic-ref HEAD {}".format(shlex.quote("refs/heads/{}".format(problem))))

    # patterns of file names to exclude
    run("git config core.excludesFile {}".format(shlex.quote(EXCLUDE)))
    run("git config core.ignorecase true")

    # adds, modifies, and removes index entries to match the working tree
    run("git add --all")

    # files that will be submitted
    files = run("git ls-files").decode("utf-8").split()
    if len(files) == 0:
        raise Error("None of the files in this directory are expected for submission.") from None
    print(termcolor.colored("Files that will be submitted:", "yellow"))
    for f in files:
        print(" {}".format(termcolor.colored(f, "yellow")))

    # files that won't be submitted
    files = run("git ls-files --other").decode("utf-8").split()
    if len(files) != 0:
        print(termcolor.colored("Files that won't be submitted:", "yellow"))
        for f in files:
            print(" {}".format(termcolor.colored(f, "yellow")))

    print(termcolor.colored("Submit? ", "yellow"), end="")
    if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
        raise Error()

    # push changes
    run("git commit --allow-empty --message='{}'".format(timestamp))
    run("git push origin 'refs/heads/{}'".format(problem))

    # create a new orphan branch and switch to it
    run("git checkout --orphan 'orphan'")
    run("git add --all")
    run("git commit --allow-empty --message='{}'".format(timestamp))

    # add a tag reference
    run("git tag --force '{}'".format(problem))
    run("git push --force origin 'refs/tags/{}'".format(problem))

    # successful submission
    teardown()
    print(termcolor.colored("Submitted {}! See https://github.com/{}/{}/tree/{}.".format(
        problem, ORG_NAME, username, problem), "green"))
    print("Academic Honesty reminder: If you commit some act that is not reasonable but bring it to the attention of the course’s heads within 72 hours, the course may impose local sanctions that may include an unsatisfactory or failing grade for work submitted, but the course will not refer the matter for further disciplinary action except in cases of repeated acts.")

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
        username, password, email, github = authenticate()
    except:
        raise Error("Invalid username and/or password.") from None

    # get student names if none provided
    if usernames == None:
        usernames = []
        for repo in github.organization(ORG_NAME).repositories():
            if repo.name != ORG_NAME:
                usernames.append(repo.name)

    # clone repositories
    for name in usernames:

        # check whether name exists in filesystem
        if os.path.exists(name):

            # check whether name is a directory
            if os.path.isfile(name):
                print("Not a directory: {}".format(name))
                continue

            # pull repository
            url = pexpect.run("git config --get remote.origin.url", cwd=name).decode("utf-8")
            if url == "":
                print("Missing origin: {}".format(name))
                continue
            if not url.startswith("https://{}@github.com/{}/".format(username, ORG_NAME)):
                print("Invalid repo: {}".format(name))
            pexpect.run("git pull", cwd=name)
        else:
            # clone repository if it doesn't already exist
            pexpect.run("git clone 'https://{}@github.com/submit50/{}' '{}'".format(username, name, name))

        # if no problem specified, don't switch branches
        if problem == None:
            continue

        # check out branch
        branches = pexpect.run("git branch -r", cwd=name).decode("utf-8")
        if "origin/{}".format(problem) in branches:
            branches = pexpect.run("git branch", cwd=name).decode("utf-8")
            if problem in branches:
                pexpect.run("git checkout '{}'".format(problem), cwd=name)
            else:
                pexpect.run("git checkout --track 'origin/{}'".format(problem), cwd=name)
        else:
            branches = pexpect.run("git branch", cwd=name).decode("utf-8")
            if problem in branches:
                pexpect.run("git checkout '{}'".format(problem), cwd=name)
            else:
                pexpect.run("git checkout -b'{}'".format(problem), cwd=name)
                pexpect.run("git rm -rf .", cwd=name)

    teardown()

# deletes temporary directory and temporary file
def teardown():
    run("rm -rf '{}'".format(run.GIT_DIR))
    if EXCLUDE:
        run("rm -f '{}'".format(EXCLUDE))

def run(command, password=None, cwd=None):
    print(command)
    if password:
        child = pexpect.spawnu(command, env={
            "GIT_DIR": run.GIT_DIR, "GIT_WORK_TREE": run.GIT_WORK_TREE
        }, cwd=cwd)
        child.logfile_read = sys.stdout
        child.expect("Password.*:")
        child.sendline(password)
        try:
            child.expect(pexpect.EOF)
        except:
            pass
        child.close()
    else:
        return pexpect.run(command, env={
            "GIT_DIR": run.GIT_DIR, "GIT_WORK_TREE": run.GIT_WORK_TREE
        }, cwd=cwd)
run.GIT_DIR = tempfile.mkdtemp()
run.GIT_WORK_TREE = os.getcwd()

def two_factor_callback():
    """Get one-time authentication code."""
    # send authentication request
    requests.post("https://api.github.com/authorizations", auth=two_factor_callback.auth, data={"scopes":["repo", "user"]})
    while True:
        print("Authentication Code: ", end="", flush=True)
        code = input()
        if code:
            break
    return code
two_factor_callback.auth = None

def usage():
    print("Usage: submit50 problem")

if __name__ == "__main__":
    main()
