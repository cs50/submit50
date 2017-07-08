from __future__ import print_function

import argparse
import atexit
import datetime
import distutils
import itertools
import json
import os
import pexpect
import pipes
import re
import readline
import requests
import select
import shlex
import shutil
import signal
import subprocess
import sys
import termcolor
import tempfile
import textwrap
import time
import traceback

from backports.shutil_get_terminal_size import get_terminal_size
from backports.shutil_which import which
from distutils.spawn import find_executable
from distutils.version import StrictVersion
from pkg_resources import DistributionNotFound, get_distribution, parse_version
from six.moves import urllib
from threading import Thread

# require python 2.7+
if sys.version_info < (2, 7):
    sys.exit("You have an old version of python. Install version 2.7 or higher.")
if sys.version_info < (3, 0):
    input = raw_input
if not hasattr(shlex, "quote"):
    shlex.quote = pipes.quote

# globals
ORG = "submit50"
timestamp = None


class Error(Exception):
    """Exception raised for errors."""
    pass


class _Getch:
    """
    Get a single character from standard input.

    https://stackoverflow.com/a/510364
    """

    class _GetchUnix:
        def __init__(self):
            import tty, sys

        def __call__(self):
            import sys, termios, tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    class _GetchWindows:
        def __init__(self):
            import msvcrt

        def __call__(self):
            import msvcrt
            return msvcrt.getch()

    def __init__(self):
        try:
            self.impl = _Getch._GetchWindows()
        except ImportError:
            self.impl = _Getch._GetchUnix()

    def __call__(self):
        return self.impl()


getch = _Getch()


# submit50
def main():

    # listen for ctrl-c
    signal.signal(signal.SIGINT, handler)

    # clean up on normal exit
    atexit.register(teardown)

    # define command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="show commands being executed")
    parser.add_argument("--no-upgrade", action="store_true")
    parser.add_argument("problem", help="problem to submit")
    args = vars(parser.parse_args())

    # check if installed as a package
    try:
        distribution = get_distribution("submit50")
    except DistributionNotFound:
        distribution = None

    # check for newer version on PyPi
    if distribution:
        res = requests.get("https://pypi.python.org/pypi/submit50/json")
        pypi = res.json() if res.status_code == 200 else None
        version = StrictVersion(distribution.version)
        if pypi and not args["no_upgrade"] or StrictVersion(pypi["info"]["version"]) > version:

            # update submit50
            pip = "pip3" if sys.version_info >= (3, 0) else "pip"
            status = subprocess.call([pip, "install", "--upgrade", "submit50"])

            # if update succeeded, re-run submit50
            if status == 0:
                submit50 = os.path.realpath(__file__)
                os.execv(submit50, sys.argv + ["--no-upgrade"])
            else:
                cprint("Could not update submit50.", "yellow", file=sys.stderr)

    # submit50 -v
    # submit50 --verbose
    if args["verbose"]:
        run.verbose = True

    # submit50 problem
    submit("submit50", args["problem"])

    # kthxbai
    sys.exit(0)


def authenticate(org):
    """Authenticate user."""

    # cache credentials in ~/.git-credential-cache/submit50
    cache = os.path.expanduser("~/.git-credential-cache")
    try:
        os.mkdir(cache, 0o700)
    except:
        pass
    socket = os.path.join(cache, ORG)

    # check cache, then config for credentials
    credentials = run("git -c credential.helper='cache --socket {}' credential fill".format(socket),
                      lines=[""]*3,
                      quiet=True)
    run("git credential-cache --socket {} exit".format(socket))
    matches = re.search("^username=([^\r]+)\r\npassword=([^\r]+)\r?$", credentials, re.MULTILINE)
    if matches:
        username = matches.group(1)
        password = matches.group(2)
    else:
        try:
            username = run("git config --global credential.https://github.com/submit50.username")
        except:
            username = None
        password = None

    def rlinput(prompt, prefill=""):
        """
        Input function that uses a prefill value and advanced line editing.

        https://stackoverflow.com/a/2533142
        """
        readline.set_startup_hook(lambda: readline.insert_text(prefill))
        try:
            return input(prompt)
        finally:
           readline.set_startup_hook()

    # prompt for credentials
    spin(False) # because not using cprint herein
    if not password:

        # prompt for username, prefilling if possible
        while True:
            spin(False)
            username = rlinput("GitHub username: ", username).strip()
            if username:
                break

        # prompt for password
        while True:
            print("GitHub password: ", end="", flush=True)
            password = str()
            while True:
                ch = getch()
                if ch in ["\n", "\r"]: # Enter
                    print()
                    break
                elif ch == "\177": # DEL
                    if len(password) > 0:
                        password = password[:-1]
                        print("\b \b", end="", flush=True)
                elif ch == "\3": # ctrl-c
                    print("^C", end="")
                    os.kill(os.getpid(), signal.SIGINT)
                else:
                    password += ch
                    print("*", end="", flush=True)
            if password:
                break

    # authenticate user
    email = "{}@users.noreply.github.com".format(username)
    res = requests.get("https://api.github.com/user",
                       auth=(username, password))

    # check for 2-factor authentication
    # http://github3.readthedocs.io/en/develop/examples/oauth.html?highlight=token
    if "X-GitHub-OTP" in res.headers:
        password = two_factor(org, username, password)
        res = requests.get("https://api.github.com/user",
                           auth=(username, password))

    # check if incorrect password
    if res.status_code == 401:
        raise Error("Invalid username and/or password.")

    # check for other error
    elif res.status_code != 200:
        raise Error("Could not authenticate user.")

    # canonicalize (capitalization of) username,
    # especially if user logged in via email address
    username = res.json()["login"]

    # cache credentials for 1 week
    timeout = int(datetime.timedelta(weeks=1).total_seconds())
    run("git -c credential.helper='cache --socket {} --timeout {}' "
        "-c credentialcache.ignoresighup=true credential approve".format(socket, timeout),
        lines=["username={}".format(username), "password={}".format(password), "", ""],
        quiet=True)

    # return credentials
    return (username, password, email)


def cprint(text="", color=None, on_color=None, attrs=None, **kwargs):
    """Colorizes text (and wraps to terminal's width)."""

    # stop spinner (if spinning)
    spin(False)

    # assume 80 in case not running in a terminal
    columns, _ = get_terminal_size()
    if columns == 0: columns = 80 # because get_terminal_size's default fallback doesn't work in pipes

    # only python3 supports "flush" keyword argument
    if sys.version_info < (3, 0) and "flush" in kwargs:
        del kwargs["flush"]

    # print text
    termcolor.cprint(textwrap.fill(text, columns, drop_whitespace=False),
                     color=color, on_color=on_color, attrs=attrs, **kwargs)


def excepthook(type, value, tb):
    """Report an exception."""
    excepthook.ignore = False
    spin(False)
    teardown()
    if type is Error and str(value):
        cprint(str(value), "yellow")
    elif type is requests.exceptions.ConnectionError:
        cprint("Could not connect to GitHub.", "yellow")
    else:
        if run.verbose:
            traceback.print_exception(type, value, tb)
        cprint("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "yellow")
    cprint("Submission cancelled.", "red")


sys.excepthook = excepthook


def handler(number, frame):
    """Handle SIGINT."""
    os.system("stty sane") # in case signalled from input_with_prefill
    if spin.spinning:
        spin(False)
    else:
        cprint()
    cprint("Submission cancelled.", "red")
    os._exit(0)


def run(command, cwd=None, env=None, lines=[], password=None, quiet=False):
    """Run a command."""

    # echo command
    if run.verbose:
        cprint(command, attrs=["bold"])

    # include GIT_DIR and GIT_WORK_TREE in env
    if not env:
        env = {
            "GIT_DIR": run.GIT_DIR,
            "GIT_WORK_TREE": run.GIT_WORK_TREE,
            "HOME": os.path.expanduser("~")
        }

    # spawn command
    if sys.version_info < (3, 0):
        child = pexpect.spawn(command, cwd=cwd, env=env, ignore_sighup=True, timeout=None)
    else:
        child = pexpect.spawnu(command, cwd=cwd, encoding="utf-8", env=env, ignore_sighup=True, timeout=None)

    # send output of command to stdout only if run with --verbose (and not quieted by caller)
    if run.verbose and not quiet:
        child.logfile_read = sys.stdout

    # wait for prompt, send password
    if password:
        res = child.expect(["Password for '.*': ", pexpect.EOF])
        if res == 0:
            child.sendline(password)

    # send lines of input
    for line in lines:
        child.sendline(line)

    # read output, check status
    command_output = child.read().strip()
    child.close()
    if child.signalstatus is None and child.exitstatus != 0:
        raise Error()
    return command_output


run.GIT_DIR = tempfile.mkdtemp()
run.GIT_WORK_TREE = os.getcwd()
run.verbose = False


def spin(message=""):
    """Display a spinning message."""

    # don't spin in verbose mode
    if run.verbose:
        if message != False:
            print(message + "...")
        return

    # stop spinning if already spinning
    if spin.spinning:
        spin.spinning = False
        spin.thread.join()

    # start spinning if message passed
    if message != False:
        def spin_helper(): # https://stackoverflow.com/a/4995896
            spinner = itertools.cycle(["-", "\\", "|", "/"])
            sys.stdout.write(message + "... ")
            sys.stdout.flush()
            while spin.spinning:
                sys.stdout.write(next(spinner))
                sys.stdout.flush()
                sys.stdout.write("\b")
                time.sleep(0.1)
            sys.stdout.write("\033[2K\r")
            sys.stdout.flush()
        spin.spinning = True
        spin.thread = Thread(target=spin_helper)
        spin.thread.start()


spin.spinning = False


def submit(org, problem):
    """Submit problem."""

    # require git 2.7+, so that credential-cache--daemon ignores SIGHUP
    # https://github.com/git/git/blob/v2.7.0/credential-cache--daemon.c
    if not which("git"):
        raise Error("You don't have git. Install git, then re-run submit50!.")
    version = subprocess.check_output(["git", "--version"]).decode("utf-8")
    matches = re.search(r"^git version (\d+\.\d+\.\d+).*$", version)
    if not matches or StrictVersion(matches.group(1)) < StrictVersion("2.7.0"):
        raise Error("You have an old version of git. Install version 2.7 or later, then re-run submit50!")

    # update spinner
    spin("Connecting")

    # compute timestamp
    global timestamp
    headers = requests.get("https://api.github.com/").headers
    timestamp = datetime.datetime.strptime(headers["Date"], "%a, %d %b %Y %H:%M:%S %Z")
    timestamp = timestamp.strftime("%Y%m%dT%H%M%SZ")

    # check version
    res = requests.get("https://cs50.me/versions/submit50")
    if res.status_code != 200:
        raise Error("You have an unknown version of submit50. " +
                    "Email sysadmins@cs50.harvard.edu!")
    version_required = res.text.strip()
    if parse_version(version_required) > parse_version(get_distribution("submit50").version):
        raise Error("You have an old version of submit50. " +
                    "Run update50, then re-run submit50!")

    # assume cs50/ problem if problem name begins with a year
    branch = problem
    if problem.split("/")[0].isdigit():
        branch = os.path.join("cs50", problem)

    # ensure problem exists
    _, submit.EXCLUDE = tempfile.mkstemp()
    url = "https://cs50.me/excludes/{}/".format(branch)
    try:
        urllib.request.urlretrieve(url, filename=submit.EXCLUDE)
        lines = open(submit.EXCLUDE)
    except Exception as e:
        if run.verbose:
            cprint(str(e))
        e = Error("Invalid problem. Did you mean to submit something else?")
        e.__cause__ = None
        raise e

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
        cprint("You seem to be missing these files:")
        for pattern in missing:
            cprint(" {}".format(pattern))
        raise Error("Ensure you have the required files before submitting.")

    # update spinner
    spin("Authenticating")

    # authenticate user via SSH
    try:
        assert which("ssh")
        username, password = run("git config --global credential.https://github.com/submit50.username", quiet=True), None
        email = "{}@users.noreply.github.com".format(username)
        repo = "git@github.com:{}/{}.git".format(org, username)
        with open(os.devnull, "w") as DEVNULL:
            spin(False)
            assert subprocess.call(["ssh", "git@github.com"], stderr=DEVNULL) == 1 # successfully authenticated

    # authenticate user via HTTPS
    except:
        username, password, email = authenticate(org)
        repo = "https://{}@github.com/{}/{}".format(username, org, username)

    # update spinner
    spin("Preparing")

    # clone repository
    try:
        run("git clone --bare {} {}".format(shlex.quote(repo), shlex.quote(run.GIT_DIR)), password=password)
    except:
        if password:
            e = Error("Looks like submit50 isn't enabled for your account yet. " +
                      "Log into https://cs50.me/ in a browser, click \"Authorize application\", and re-run submit50 here!")
        else:
            e = Error("Looks like you have the wrong username in ~/.gitconfig or submit50 isn't yet enabled for your account. " +
                      "Double-check ~/.gitconfig and then log into https://cs50.me/ in a browser, " +
                      "click \"Authorize application\" if prompted, and re-run submit50 here.")
        e.__cause__ = None
        raise e

    # set options
    tag = "{}@{}".format(branch, timestamp)
    run("git config user.email {}".format(shlex.quote(email)))
    run("git config user.name {}".format(shlex.quote(username)))
    run("git symbolic-ref HEAD refs/heads/{}".format(shlex.quote(branch)))

    # patterns of file names to exclude
    run("git config core.excludesFile {}".format(shlex.quote(submit.EXCLUDE)))

    # adds, modifies, and removes index entries to match the working tree
    run("git add --all")

    # get file lists
    files = run("git ls-files").split()
    other = run("git ls-files --other").split()

    # files that will be submitted
    if len(files) == 0:
        raise Error("No files in this directory are expected for submission.")
    cprint("Files that will be submitted:", "green")
    for f in files:
        cprint("./{}".format(f), "green")

    # files that won't be submitted
    if len(other) != 0:
        cprint("Files that won't be submitted:", "yellow")
        for f in other:
            cprint("./{}".format(f), "yellow")

    # prompt for academic honesty
    cprint("Keeping in mind the course's policy on academic honesty, " +
           "are you sure you want to submit these files?", end=" ")
    if not re.match("^\s*(?:y|yes)\s*$", input(), re.I):
        raise Error("No files were submitted.")

    # restart spinner
    spin("Submitting")

    # push branch
    run("git commit --allow-empty --message='{}'".format(timestamp))
    run("git push origin 'refs/heads/{}'".format(branch), password=password)

    # successful submission
    cprint("Submitted {}! ".format(problem) +
           "See https://cs50.me/submissions/{}.".format(branch),
           "green")


submit.EXCLUDE = None


def teardown():
    """Delete temporary directory and temporary file."""
    shutil.rmtree(run.GIT_DIR, ignore_errors=True)
    if submit.EXCLUDE:
        try:
            os.remove(submit.EXCLUDE)
        except Exception:
            pass


def two_factor(org, username, password):
    """Get one-time authentication code."""
    # send authentication request
    requests.post("https://api.github.com/authorizations",
                  auth=(username, password))
    while True:
        cprint("Authentication code:", end=" ", flush=True)
        code = input()
        if code:
            break
    data = json.dumps({"scopes": ["repo", "user"], "note": "{} {}".format(org, timestamp)})
    res = requests.post("https://api.github.com/authorizations",
                        auth=(username, password),
                        data=data,
                        headers={"X-GitHub-OTP": str(code)})
    if res.status_code == 201 and "token" in res.json():
        return res.json()["token"]
    else:
        raise Error("Could not complete two-factor authentication.")


if __name__ == "__main__":
    main()
