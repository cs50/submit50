#!/usr/bin/python3

import datetime
import getch
import github3
import http.client
import json
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
timestamp = ""

class Error(Exception):
    """Exception raised for errors."""
    pass

# submit50
def main():

    # listen for ctrl-c
    signal.signal(signal.SIGINT, handler)
    
    # compute timestamp
    headers = requests.get("https://api.github.com/").headers
    global timestamp
    timestamp = datetime.datetime.strptime(headers["Date"], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=pytz.utc)
    timestamp = timestamp.astimezone(pytz.timezone("America/New_York")).strftime("%a, %d %b %Y %H:%M:%S %Z")

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
    two_factor.auth = (username, password)
    github = github3.login(username, password, two_factor_callback=two_factor)
    email = "{}@users.noreply.github.com".format(username)
    
    # check for 2-factor authentication
    # http://github3.readthedocs.io/en/develop/examples/oauth.html?highlight=token
    res = requests.post("https://api.github.com/user", auth=(username, password))
    if "X-GitHub-OTP" in res.headers:
        two_factor()
        password = two_factor.token
    
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
        call.process.kill()
        call.process = None
        return None
call.process = None

def excepthook(type, value, tb):
    """Report an exception."""
    teardown()
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
    teardown()
    if call.process:
        call.process.kill()
    print()
    sys.exit(0)

def submit(problem):
    """Submit problem."""

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
        username, password, email = authenticate()
    except:
        raise Error("Invalid username and/or password.") from None

    # check for submit50 repository
    res = requests.get("https://api.github.com/repos/{}/{}".format(ORG_NAME, username), auth=(username, password))
    repository = res.status_code == 200
    if not repository:
        raise Error("Looks like we haven't enabled submit50 for your account yet! Let sysadmins@cs50.harvard.edu know your GitHub username!")

    # clone submit50 repository
    run("git clone --bare {} {}".format(
    shlex.quote("https://{}@github.com/{}/{}".format(username, ORG_NAME, username)),
        shlex.quote(run.GIT_DIR)
    ), password=password)

    # set options
    run("git config user.email {}".format(shlex.quote(email)))
    run("git config user.name {}".format(shlex.quote(username)))
    run("git symbolic-ref HEAD {}".format(shlex.quote("refs/heads/{}".format(problem))))

    # patterns of file names to exclude
    run("git config core.excludesFile {}".format(shlex.quote(EXCLUDE)))
    run("git config core.ignorecase true")

    # adds, modifies, and removes index entries to match the working tree
    run("git add --all")

    # get file lists
    files = run("git ls-files").decode("utf-8").split()
    other = run("git ls-files --other").decode("utf-8").split()

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

    print(termcolor.colored("Submit? ", "yellow"), end="")
    if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
        raise Error()

    # push changes
    run("git commit --allow-empty --message='{}'".format(timestamp))
    run("git push origin 'refs/heads/{}'".format(problem), password=password)

    # create a new orphan branch and switch to it
    run("git checkout --orphan 'orphan'")
    run("git add --all")
    run("git commit --allow-empty --message='{}'".format(timestamp))

    # add a tag reference
    run("git tag --force '{}'".format(problem))
    run("git push --force origin 'refs/tags/{}'".format(problem), password=password)

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

# deletes temporary directory and temporary file
def teardown():
    run("rm -rf '{}'".format(run.GIT_DIR))
    if EXCLUDE:
        run("rm -f '{}'".format(EXCLUDE))

def run(command, password=None, cwd=None, env=None):
    print(command)
    if env == None:
        env = {
            "GIT_DIR": run.GIT_DIR, "GIT_WORK_TREE": run.GIT_WORK_TREE
        }
    if password:
        child = pexpect.spawnu(command, env=env, cwd=cwd)
        child.logfile_read = sys.stdout
        child.expect("Password.*:")
        child.sendline(password)
        try:
            child.expect(pexpect.EOF)
        except:
            pass
        child.close()
    else:
        return pexpect.run(command, env=env, cwd=cwd)
run.GIT_DIR = tempfile.mkdtemp()
run.GIT_WORK_TREE = os.getcwd()

def two_factor():
    """Get one-time authentication code."""
    # send authentication request
    requests.post("https://api.github.com/authorizations", auth=two_factor.auth, data={"scopes":["repo", "user"]})
    while True:
        print("Authentication Code: ", end="", flush=True)
        code = input()
        if code:
            break
    data = json.dumps({"scopes":["repo", "user"], "note":"{} {}".format(ORG_NAME, timestamp)})
    res = requests.post("https://api.github.com/authorizations", auth=two_factor.auth,
        data=data,
        headers={"X-GitHub-OTP": str(code)})
    if "token" in res.json():
        two_factor.token = res.json()["token"]
    else:
        raise Error("Could not complete two-factor authentication.") from None
    return code
two_factor.auth = None
two_factor.token = None

def usage():
    print("Usage: submit50 problem")

if __name__ == "__main__":
    main()