#!/usr/bin/env python3
import argparse
import enum
import gettext
import logging
import os
import re
import shutil
import sys
import textwrap
import traceback

import lib50
import requests
import termcolor

from importlib.resources import files
from packaging import version
from datetime import datetime
from pytz import timezone
from . import __version__, CONFIG_LOADER

# Internationalization
gettext.install("submit50", str(files("submit50").joinpath("locale")))

LOGGER = logging.getLogger("submit50")

SUBMIT_URL = "https://submit.cs50.io"

class LogLevel(enum.IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "ERROR": "red",
        "WARNING": "yellow",
        "DEBUG": "cyan",
        "INFO": "magenta",
    }

    def __init__(self, fmt, use_color=True):
        super().__init__(fmt=fmt)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        return msg if not self.use_color else termcolor.colored(msg, getattr(record, "color", self.COLORS.get(record.levelname)))


class Error(Exception):
    pass


def check_announcements(timeout=5):
    """Check for any announcements from submit.cs50.io, raise Error if so."""
    try:
        res = requests.get(f"{SUBMIT_URL}/status/submit50", timeout=timeout)
    except requests.RequestException:
        # Being unable to check is not an announcement; don't block the submission
        cprint(_("Could not reach submit.cs50.io to check for announcements. Continuing anyway."), "yellow")
        return
    if res.status_code == 200 and res.text.strip():
        raise Error(res.text.strip())


def check_version(package_name=__package__, timeout=5):
    """
    Check that submit50 is the latest version according to submit.cs50.io and PyPI.

    Only submit.cs50.io reporting that this version is too old blocks the submission.
    If the check itself can't be completed, warn and continue.
    """
    # Not installed as a package (e.g. running from source): nothing to compare against
    try:
        current = version.parse(__version__)
    except version.InvalidVersion:
        return

    # Minimum required version according to submit.cs50.io
    try:
        res = requests.get(f"{SUBMIT_URL}/versions/submit50", timeout=timeout)
        res.raise_for_status()
        minimum = version.parse(res.text.strip())
    except (requests.RequestException, version.InvalidVersion):
        cprint(_("Could not check whether {} is up to date. Continuing anyway.").format(package_name), "yellow")
        return

    if current < minimum:
        raise Error(_("Current version {} of {} is no longer supported. Run \"pip3 install --upgrade {}\" now to upgrade.")
                    .format(current, package_name, package_name))

    # Latest version on PyPI, only to suggest an upgrade
    try:
        res = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=timeout)
        res.raise_for_status()
        latest_pypi = max(version.parse(release) for release in res.json()["releases"])
    except (requests.RequestException, ValueError, KeyError, TypeError, version.InvalidVersion):
        return

    if latest_pypi > current:
        cprint(_("A newer version of {} is available. Run \"pip3 install --upgrade {}\" now to upgrade.")
               .format(package_name, package_name), "magenta")


def setup_logging(level):
    """
    Sets up logging for lib50.
    level 'info' logs all git commands run to stderr
    level 'debug' logs all git commands and their output to stderr
    """
    logger = logging.getLogger("lib50")

    # Set verbosity level on the lib50 logger
    logger.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColoredFormatter("(%(levelname)s) %(message)s", use_color=sys.stderr.isatty()))

    # Direct all logs to sys.stderr
    logger.addHandler(handler)

    # Don't animate the progressbar if LogLevel is either info or debug
    lib50.ProgressBar.DISABLED = logger.level < LogLevel.WARNING

    # Show exceptions when debugging
    excepthook.verbose = logger.level == LogLevel.DEBUG


def cprint(text="", color=None, on_color=None, attrs=None, **kwargs):
    """Colorizes text (and wraps to terminal's width)."""

    # Handle invalid UTF-8 characters
    text = text.encode('utf-8', 'replace').decode('utf-8')
    # Assume 80 in case not running in a terminal
    columns, lines = shutil.get_terminal_size()
    if columns == 0:
        columns = 80  # Because get_terminal_size's default fallback doesn't work in pipes

    # Print text
    termcolor.cprint(textwrap.fill(text, columns, drop_whitespace=False),
                     color=color, on_color=on_color, attrs=attrs, **kwargs)


def prompt(honesty, included, excluded):
    if included:
        cprint(_("Files that will be submitted:"), "green")
        for file in included:
            cprint("./{}".format(file), "green")
    else:
        raise Error(_("No files in this directory are expected for submission."))

    # Files that won't be submitted
    if excluded:
        cprint(_("Files that won't be submitted:"), "yellow")
        for other in excluded:
            cprint("./{}".format(other), "yellow")

    # If there's no honesty question, continue.
    if not honesty:
        return True

    # Prompt for honesty
    try:
        # Show default message
        if honesty == True:
            honesty_question = _(
                "Keeping in mind the course's policy on academic honesty, including its restrictions on AI use, "
                "are you sure you want to submit these files (yes/no)? "
            )
        # If a custom message is configured, show that instead
        else:
            honesty_question = str(honesty)

        # Get the user's answer
        # If in R Studio environment, answer is always yes
        if os.getenv("RSTUDIO") == "1":
            answer = "yes"
        else:
            answer = input(honesty_question)
    except EOFError:
        answer = None
        print()

    # If no answer given, or yes is not given, don't continue
    if not answer or not re.match(f"^\s*(?:{_('y|yes')})\s*$", answer, re.I):
        return False

    # Otherwise, do continue
    return True


def check_slug_year(slug):
    """Warn if the slug is for previous year's CS50x course."""

    # extract the year from the slug
    try:
        year = re.search(r"cs50/problems/(\d{4})/x", slug)
        if year and int(year.group(1)) < int(datetime.now(timezone("US/Eastern")).year):
            suggested_slug = re.sub(r"cs50/problems/\d{4}/x", f"cs50/problems/{datetime.now(timezone('US/Eastern')).year}/x", slug)
            cprint(_("You are submitting to a previous year's CS50x course. Your submission will not be counted towards this year's course."), "yellow")
            cprint(_("If you are looking to submit to this year's course, please use the following slug:"), "yellow")
            cprint(suggested_slug, "yellow")

            # Ask if they want to continue
            if not re.match(f"^\s*(?:{_('y|yes')})\s*$", input(_("Do you want to continue with this submission (yes/no)? ")), re.I):
                raise Error(_("User aborted submission."))

    except ValueError:
        pass


def excepthook(type, value, tb):
    """Report an exception."""
    if (issubclass(type, Error) or issubclass(type, lib50.Error)) and str(value):
        for line in str(value).split("\n"):
            cprint(str(line), "yellow")
    elif not isinstance(value, KeyboardInterrupt):
        cprint(_("Sorry, something's wrong, please try again. If the problem persists, please visit our status page https://cs50.statuspage.io for more information."), "yellow")

    if excepthook.verbose:
        traceback.print_exception(type, value, tb)

    cprint(_("Submission cancelled."), "red")

excepthook.verbose = True


class LogoutAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=_("logout of submit50")):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            lib50.logout()
        except lib50.Error:
            raise Error(_("failed to logout"))
        else:
            cprint(_("logged out successfully"), "green")
        parser.exit()


def main():
    sys.excepthook = excepthook

    parser = argparse.ArgumentParser(prog="submit50")
    parser.add_argument("--logout", action=LogoutAction)
    parser.add_argument(
        "--log-level",
        action="store",
        default="warning",
        choices=[level.name.lower() for level in LogLevel],
        type=str.lower,
        help=_('warning: displays usage warnings.'
                '\ninfo: adds all commands run.'
                '\ndebug: adds the output of all commands run.')
    )
    parser.add_argument("--https",
                        action="store_true",
                        help=_("force authentication via HTTPS"))
    parser.add_argument("--ssh",
                        action="store_true",
                        help=_("force authentication via SSH"))
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "slug",
        help=_("prescribed identifier of work to submit")
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    check_announcements()
    check_version()
    check_slug_year(args.slug)

    # Decide whether to force HTTPS or SSH authentication
    if args.https and args.ssh:
        LOGGER.warning(_("--https and --ssh have no effect when used together"))
        auth_method = None
    elif args.https:
        auth_method = "https"
    elif args.ssh:
        auth_method = "ssh"
    else:
        auth_method = None

    try:
        user_name, commit_hash, message = lib50.push("submit50", args.slug, CONFIG_LOADER, prompt=prompt, auth_method=auth_method)
    except lib50.ConnectionError:
        LOGGER.debug(traceback.format_exc()) # log the traceback
        raise Error(_(
            "check50 failed to authenticate your Github account. Try running check50 again with --https or --ssh, "
            "or try restarting your codespace. If the problem persists, please email us at sysadmins@cs50.harvard.edu."
        ))
    print(message)

if __name__ == "__main__":
    main()
